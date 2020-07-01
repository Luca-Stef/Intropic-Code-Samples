# IEX data API key pk_10e650123a8649a2857cf922305bfb3e

import os

import sqlite3
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
#app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure SQLite database
connection = sqlite3.connect('finance.db')
connection.row_factory = sqlite3.Row
db = connection.cursor()

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":

        # Query database and create list of dictionaries to be added to index.html as rows
        sqlresponse = db.execute("select symbol, sum(quantity) from transactions where user_id=:user_id group by symbol", {"user_id": session["user_id"]}).fetchall()
        portfolio = [{"stock": row["symbol"], "quantity": int(row["sum(quantity)"]), "price": usd(lookup(row["symbol"])["price"]),
                      "marketcap": usd(lookup(row["symbol"])["price"] * row["sum(quantity)"])} for row in sqlresponse]

        # Get user cash balance and net worth or account
        cash = db.execute("select cash from users where id=:user_id", {"user_id": session["user_id"]}).fetchall()[0]["cash"]
        net = cash
        for row in portfolio:

            # This reverses the usd function and adds it to net
            net += float(row["marketcap"][1:].replace(',',''))

        return render_template("index.html", portfolio=portfolio, net=usd(net), cash=usd(cash))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":
        return render_template("buy.html")

    # User reached route via POST (as by submitting a form via POST)
    else:

        # Verify non empty string input and lookup function return value
        if not request.form.get("symbol") or lookup(request.form.get("symbol")) == None:
            return render_template("buy.html", message = "Invalid symbol")

        # String must be numeric
        if not request.form.get("shares").isnumeric():
            return render_template("buy.html", message="Quantity must be a number")

        # Verify positive integer input for quantity of shares
        if int(request.form.get("shares")) <= 0 or int(request.form.get("shares")) % 1 != 0:
            return render_template("buy.html", message = "Quantity of shares must be a positive integer")

        # Set variables for transaction
        quote = lookup(request.form.get("symbol"))
        cash = db.execute("select cash from users where id=:id", {"id": session["user_id"]}).fetchall()[0]["cash"]
        price = quote["price"]
        quantity = int(request.form.get("shares"))

        # Do not allow negative balance
        if price * quantity > cash:
            return render_template("buy.html", message=f"Cannot afford {quantity} {quote['name']} shares. Current balance: {usd(cash)}")

        # update balance
        cash -= price * quantity
        db.execute("update users set cash=:cash where id=:id", {"cash": cash, "id": session["user_id"]})

        # Get date and time string
        now = datetime.now().strftime("%d-%m-%Y %H:%M:%S.%f")

        # Insert into transactions table
        db.execute("insert into transactions (user_id, symbol, price, quantity, date) values (:user_id, :symbol, :price, :quantity, :date)",
                   {"user_id": session["user_id"], "symbol": quote["symbol"], "price": price, "quantity": quantity, "date": now})

        return render_template("buy.html", message=f"{quantity} {quote['name']} added to your account")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    # Query database for all transactions associated with current usesr
    history = db.execute("select symbol, price, quantity, date from transactions where user_id=:user_id order by date desc", {"user_id": session["user_id"]}).fetchall()

    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":

        # Render history.html with history of transactions
        return render_template("history.html", history=history)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("login.html", message="Must provide username.")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("login.html", message="Must provide password.")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", {"username": request.form.get("username")}).fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template("login.html", message="Invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html", message="")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Save changes
    connection.commit()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        quote = lookup(request.form.get("symbol"))

        # Display message depending on response of IEXAPI
        if quote != None:
            return render_template("quote.html", message=f"Price of {quote['name']} stock is {usd(quote['price'])}")
        else:
            return render_template("quote.html", message="Invalid symbol")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html", message="")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("register.html", message="Must provide username")

        # Ensure username is unique
        elif len(db.execute("SELECT username FROM users WHERE username=:username", {"username": request.form.get("username")}).fetchall()) != 0:
            return render_template("register.html", message="Username already exists")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("register.html", message="Must provide password")

        # Ensure password confirmation was submitted
        elif not request.form.get("confirmation"):
            return render_template("register.html", message="must confirm passworrd")

        # Ensure password match
        elif request.form.get("password") != request.form.get("confirmation"):
            return render_template("register.html", message="passwords must match")

        # Insert account information into database
        db.execute("INSERT INTO users (username, hash) values (:username, :hash)",
                   {"username": request.form.get("username"), "hash": generate_password_hash(request.form.get("password"))})

        # Remember which user has logged in
        session["user_id"] = db.execute("SELECT id FROM users where username=:username", {"username": request.form.get("username")}).fetchall()[0]['id']

        # Redirect user to home page
        redirect("/")

    # User reached the route via GET (as by clicking a link or redirect)
    else:
        return render_template("register.html", message="")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    stock = {str(i["symbol"]): int(i["sum(quantity)"]) for i in db.execute("select symbol, sum(quantity) from transactions where user_id=:user_id group by symbol;",
                                                                      {"user_id": session["user_id"]}).fetchall()}

    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":

        # Render sell.html with a list of symbols corresponding to past transactions
        return render_template("sell.html", stock=stock)

    # User reached route via POST (as by submitting a form via POST)
    else:

        # String must be numeric
        if not request.form.get("shares").isnumeric():
            return render_template("sell.html", stock=stock, message="Quantity must be a number")

        # Shares sold must be a positive integer
        if int(request.form.get("shares")) <= 0 or int(request.form.get("shares")) % 1 != 0:
            return render_template("sell.html", message = "Quantity of shares must be a positive integer")

        # Set variables from form submission
        symbol = request.form.get("symbol")
        quantity = int(request.form.get("shares"))

        # Check quantity owned
        if stock[symbol] < quantity:
            return render_template("sell.html", stock=stock, message=f"You only own {stock[symbol]} {symbol} shares")

        # Amend user cash balance record transaction in table, negative quantity indicates a sell operation
        db.execute("update users set cash=cash+:quantity where id=:id", {"quantity": quantity * lookup(symbol)["price"], "id": session["user_id"]})
        db.execute("insert into transactions (user_id, symbol, price, quantity, date) values (:user_id, :symbol, :price, :quantity, :date)",
                   {"user_id": session["user_id"], "symbol": symbol, "price": lookup(symbol)["price"], "quantity": -quantity, "date": datetime.now().strftime("%d-%m-%Y %H:%M:%S")})

        return render_template("sell.html", stock=stock, message=f"{quantity} {symbol} shares sold from your account")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)