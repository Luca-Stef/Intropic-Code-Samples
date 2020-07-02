# Intropic-Code-Samples
Code samples for Sam.

Finance is a basic flask web application that allows you to simulate buying, selling, and getting stock price quotes. You should be able to run it locally or if not just try it on the cs50 ide (https://ide.cs50.io/). From the finance directory by running export API_KEY=pk_10e650123a8649a2857cf922305bfb3e  followed by flask run. Discplaimer: some of the code was written by the cs50x teaching staff, such as layout.html and helpers.c but I read over this code and fully understand it. I hope it works fine but I have never ran it on any PC but my own and I also just switched over from CS50's SQL implementation to the standard sqlite3 which produced a ton of bugs I had to fix.

Speller is a spell checker. Texts contains a ton of text files to spell check using the large dictionary in dictionaries. Keys is just to check the checker. Run it by typing ./speller texts/aca.txt (or any other text file) I did not design the hash function. It would be a good exercise to come back to this and implement a trie data structure instead of a hash table of linked lists to store the dictionary, this would optimise searching.

Tideman is an implementation of the tideman voting algorithm which I thought was interesting because of the application of graph theory. Run it with ./tideman Alice Bob (Or any other names of candidates) and it will ask for the number of voters followed by their preferences. The tideman system models the candidates as nodes in a directed graph with the directions indicating who the winner of that pair is. A cycle in the graph indicates a draw so recursion is used to traverse the graph and check for cycles. Alternatively I could implement the depth first search algorithm but it wasn't really a priority for me.

I'd like to show you an edge detetion algorithm implementation that I'm really happy with as well but I'm assuming I've already included quite a lot.
