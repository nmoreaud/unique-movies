# Unique Movies
Find and remove duplicated movies from your database.  
This script search for movies with names that look alike or similar binary content.  
It doesn't call external services.

## Prerequisites
Install python 3.4+ from python website
This script is compatible with Linux, Windows or MacOS

## Usage
Copy this script somewhere on your computer (ex: in your movies root directory), then from a terminal, either:
* Run `python unique-movies.py` to get a list of duplicates of current directory
* Run `python unique-movies.py path\to\movies\directory` to get a list of duplicates of a specific directory

To get a smaller list run the script like this: 
  * `python unique-movies.py --onlytests 'name'`
  * `python unique-movies.py --onlytests 'name_prefix'`
  * `python unique-movies.py --onlytests 'name_sim'`
  * `python unique-movies.py --onlytests 'content'`

Once the duplicate movies have been deleted, the movies list contains only false duplicates.  
You can then run `python unique-movies.py --ignore` to mark the remaining movies list as false positives.

To delete movies, either proceed manually, or use the `todelete_files` variable of the script if you have many files to handle.
