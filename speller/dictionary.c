// Implements a dictionary's functionality
#include <stdio.h>
#include <stdbool.h>
#include <string.h>
#include <strings.h>
#include <stdlib.h>
#include <ctype.h>
#include <stdint.h>
#include "dictionary.h"

// Represents a node in a hash table
typedef struct node
{
    char word[LENGTH + 1];
    struct node *next;
}
node;

// Number of buckets in hash table
const unsigned int N = 65535;

// Hash table
node *table[N];

// Length of dictionary
long long dict_size = 0;

// Returns true if word is in dictionary else false
bool check(const char *word)
{
    node *tmp = table[hash(word)];
    if (table[hash(word)] == NULL)
    {
        return false;
    }

    while (tmp != NULL)
    {
        if (!strcasecmp(tmp->word, word))
        {
            return true;
        }
        tmp = tmp->next;
    }
    return false;
}

// Hashes word to a number
unsigned int hash(const char *word)
{
    uint32_t hash = 0;
    while (*word)
    {
        hash = (*word | 0x20); //(hash << 2) ^ *word
        word++;
    }

    // return a value between 0 and 65535
    return (int)((hash >> 16) ^ (hash & 0xffff));
}

// Loads dictionary into memory, returning true if successful else false
bool load(const char *dictionary)
{
    // Open file and check pointer
    FILE *file = fopen(dictionary, "r");
    if (file == NULL)
    {
        printf("Failed to open file\n");
        return 0;
    }

    char word[LENGTH];

    // Load dictionary into memory
    while (fscanf(file, "%s", word)  != EOF)
    {
        node *n = malloc(sizeof(node));
        if (n == NULL)
        {
            printf("Failed to allocate memory for node\n");
            return 0;
        }
        strcpy(n->word, word);
        n->next = table[hash(n->word)];
        table[hash(n->word)] = n;
        dict_size++;
    }
    fclose(file);
    return true;
}

// Returns number of words in dictionary if loaded else 0 if not yet loaded
unsigned int size(void)
{
    return dict_size;
}

// Unloads dictionary from memory, returning true if successful else false
bool unload(void)
{
    node *cursor = NULL;
    node *tmp = NULL;

    for (int i = 0; i < N; i++)
    {
        cursor = table[i];

        while (cursor != NULL)
        {
            tmp = cursor;
            cursor = cursor->next;
            free(tmp);
        }
    }
    return true;
}