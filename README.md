# Unique Movies
Find and remove duplicated movies from your database.  
This script searches for movies with names that look alike or having similar binary content.  
It doesn't call external services.

## Prerequisites
Install python 3.4+ from python website.  
This script is compatible with Windows, MacOS and Linux.

## Usage
Copy `unique-movies.py` somewhere on your computer (ex: in your movies root directory), then from a terminal, either:
* Run `python unique-movies.py` to get a list of duplicates of current directory
* Run `python unique-movies.py path\to\movies\directory` to get a list of duplicates of a specific directory

To get a smaller list of duplicates, run the script like this: 
  * `python unique-movies.py --onlytests 'name'`
  * `python unique-movies.py --onlytests 'name_prefix'`
  * `python unique-movies.py --onlytests 'name_sim'`
  * `python unique-movies.py --onlytests 'content'`

Once you have deleted the duplicates, the movies list contains only false duplicates.  
You can then run `python unique-movies.py --ignore` to mark the remaining movies list as false positives.

To delete movies, either proceed manually, or use the `todelete_files` variable of the script if you have many files to handle.

## How it works

The script computes a simplified name for each movie to remove "keyword polution".  
You can check if the simplified names are correct with `python unique-movies.py --printnames`.  
You can choose new keywords to blacklist with `python unique-movies.py --printtokens`.

## Contribute

If you want to contribute, pick a task in this todolist : 
* Graphical user interface with Tkinter (or another library generaly packaged with python) in which you can :
  * delete duplicates (with a confirm button)
  * mark false positives
  * simplify file names (with 
  * edit rules (blacklist keywords, ignore subdirectory, ignore some file names, etc)
  * launch two movies side by side to compare them (ex VLC
* Merge 2 movie databases without copying the duplicates
* Decode video parts and compare them
* Blacklist keywords depending on the locale
* Installer
* Persistent cache based on files metadata
