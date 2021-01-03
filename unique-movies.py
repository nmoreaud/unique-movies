#! python3
# coding: utf-8

import glob
import re
import math
from pprint import pprint
from pathlib import Path
import unicodedata
from collections import Counter
import sys
from functools import cache
import hashlib
import difflib
import argparse
import json

ignore_patterns = ['série', 'petit ours brun', "how i met"]
ignore_extensions = ['.ass', '.srt', '.db', '.txt', '.bmp', '.jpg', '.ini', '.sh', '.py']
toremove_keywords = ['truefrench', 'vostfr', 'french', 'vf', 'fr', 'dvdrip', 'bdrip', 'hdtv', 'hd', 'brrip', 'fansub', 'hdrip', 'webdl', 'divx', '9divx', 'xvid', 'avi', 'x264', 'ac3', '1080p', '720p']
toreplace_keywords_src = ['i', 'ii', 'iii']
toreplace_keywords_dst = ['1', '2', '3']
similarity_threshold = .9


# WARNING : files listed bellow will be deleted for ever !!
todelete_files = [
    #"G:/Films/New/Bad Teacher.avi",
    #"G:/Films/Comédie/CaseDepart[2011].avi.avi",
]

delimiters_regex = re.compile(r'[._\-\+\!\,\= ]')
digit_regex = re.compile(r'[0-9]+')
# (_  _) [_ _] '_
glue_parenthesis1_regex = re.compile(r'(\(|\[|\') ')
glue_parenthesis2_regex = re.compile(r' (\)|\]|\')')

main_path = None
ignorelist_path = None
all_files = None
ignorelist = {}
newignorelist = {}
cliargs = None

@cache
def md5(file, offset, size):
    file.seek(offset)
    buffer = file.read(size)
    return hashlib.md5(buffer).digest()

def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')

def has_camel_case(s):
    return re.match('.*[a-z][A-Z].*', s)

def split_with_camel_case(s):
    s = re.sub('([A-Z][a-z]+)', r' \1', re.sub('([A-Z]+)', r' \1', s)).split()
    return s

def clean_whitespace(s):
    return ' '.join(s.split())

def glue_parenthesis(s):
    s = glue_parenthesis1_regex.sub(r'\1', s)
    s = glue_parenthesis2_regex.sub(r'\1', s)
    return s

def spinning_cursor():
    while True:
        for cursor in '|/-\\':
            yield cursor

spinner = spinning_cursor()
spinnerint = 0
def print_loadingcursor():
    global spinnerint
    spinnerint += 1
    if spinnerint % 4 != 0:
        return
    sys.stdout.write(next(spinner))
    sys.stdout.flush()
    sys.stdout.write('\b')

def readable_filesize(size_bytes):
   if size_bytes == 0:
       return "0"
   size_name = ("O", "KO", "MO", "GO", "TO")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 1)
   return "%s %s" % (s, size_name[i])

@cache
def file_size(file_path):
    return file_path.stat().st_size

"""
Number of disc (ex cd1, cd "1", disc2, disc "2", part1, part "1")
Number of film (onemovie III.avi)
"""
@cache
def number_part(clean_file_name):
    res = digit_regex.findall(' '.join(clean_file_name.split(' ')[1:]))
    return res if res else [1]

@cache
def clean_file_name(file_path):
    s = clean_file_name_aux(file_path, False)
    if len(s.split()) == 1 and has_camel_case(file_path.stem):
        s = clean_file_name_aux(file_path, True)
    return s

def clean_file_name_aux(file_path, split_camel):
    name = strip_accents(clean_whitespace(file_path.stem))

    # try remove everything after first parenthesis
    tmp = re.sub(r'(\[|\().+', "", name)
    if len(tmp) > 5:
        removed_parenthesis = True
        name = tmp
    else:
        removed_parenthesis = False
        name = name.replace('(', ' ( ') \
                   .replace('[', ' [ ') \
                   .replace(')', ' ) ') \
                   .replace(']', ' ] ')

    name = clean_whitespace(name)
    parts = delimiters_regex.split(name)
    if not parts:
        return []

    tmp = split_with_camel_case(' '.join(parts))
    if split_camel and len(tmp) > 1:
        parts = tmp

    parts = [part.lower() for part in parts]
    first_part = parts[0]
    other_parts = [part for part in parts[1:]]

    # try remove everything after the first toremove keyword
    removed_keywords = False
    if not first_part in toremove_keywords:
        strlen = len(first_part)
        for i, part in enumerate(other_parts):
            if part in toremove_keywords:
                if strlen > 5:
                    if i == 0:
                        return clean_whitespace(first_part)
                    other_parts = other_parts[0:i]
                    removed_keywords = True
                break
            else:
                strlen += len(part)

    other_parts = [part for part in other_parts if part not in toremove_keywords]
    # remove definition and year
    other_parts = [re.sub(r'\(\d\d\d\d\)|\[\d\d\d\d\]|^\d\d\d\d$', '', part) for part in other_parts]
    other_parts = [part for part in other_parts if len(part) > 0]

    name = ' '.join([first_part] + other_parts)
    name = glue_parenthesis(clean_whitespace(name))
    name = re.sub(r'\[\]', '', name)
    name = re.sub(r'\(\)', '', name)
    name = ' '.join([part if not part in toreplace_keywords_src else toreplace_keywords_dst[toreplace_keywords_src.index(part)] for part in name.split(' ')])
    return name

def print_cleaned_names(all_files):
    all_files = sorted(all_files, key=clean_file_name)
    for file_path in all_files:
        clean = clean_file_name(file_path)
        #numberpart = " (" + ' '.join(map(str, number_part(clean_file_name(file_path)))) + ")"
        print("{:<40} {:<200}".format(clean.capitalize(), file_path.stem))

def print_token_stats(all_files):
    tokens = {}
    for file_path in all_files:
        for token in clean_file_name(file_path).split():
            # number (ex : cd 2)
            if len(token) <= 2 and token.isdigit():
                continue
            tokens[token] = tokens.get(token, 0) + 1
    pprint(dict(Counter(tokens).most_common(cliargs.printtokens)), sort_dicts=False)

def test_same_name(file_path1, file_path2):
    return clean_file_name(file_path1) == clean_file_name(file_path2)

def test_same_name_prefix(file_path1, file_path2):
    clean1 = clean_file_name(file_path1)
    clean2 = clean_file_name(file_path2)
    number_part1 = set(number_part(clean1))
    number_part2 = set(number_part(clean2))

    if not number_part1.intersection(number_part2):
        return False

    return clean1.startswith(clean2) or clean2.startswith(clean1) or \
           clean1.endswith(clean2) or clean2.endswith(clean1)

def test_same_name_sim(file_path1, file_path2):
    clean1 = clean_file_name(file_path1)
    clean2 = clean_file_name(file_path2)
    number_part1 = set(number_part(clean1))
    number_part2 = set(number_part(clean2))

    if not number_part1.intersection(number_part2):
        return False
    return difflib.SequenceMatcher(None, clean1, clean2).ratio() > similarity_threshold

def test_same_content(file_path1, file_path2):
    size1 = file_size(file_path1)
    size2 = file_size(file_path2)
    maxsize = max(size1, size2)
    minsize = min(size1, size2)
    if minsize == 0 and maxsize != 0:
        return False
    if maxsize - minsize > 1024*300: # 300Ko of metadata may be different
        return False

    if minsize <= 8*1024*1024:
        return maxsize == minsize

    with open(file_path1, "rb") as file1:
        with open(file_path2, "rb") as file2:
            compsize = 1024

            # start from the end, metadata at the beginning
            similar = True
            for i in range(1,4):
                offset = math.ceil(minsize*i/5)
                if md5(file1, size1-offset, compsize) != md5(file2, size2-offset, compsize):
                    similar = False
                    break

            if similar:
                return True

            similar = True
            # start from the beginning, metadata at the end
            for i in range(1,4):
                offset = math.ceil(minsize*i/5)
                if md5(file1, offset, compsize) != md5(file2, offset, compsize):
                    similar = False
                    break

    return similar

@cache
def relative_to_main(file):
    return file.relative_to(main_path)

def print_duplicated_byfn(all_files, already_displayed, testname, testfn):
    for file_path1 in all_files:
        if str(file_path1) in already_displayed:
            continue

        print_loadingcursor()
        relative1 = str(relative_to_main(file_path1))
        false_dupsof_file1 = ignorelist.get(relative1, [])
        newfalse_dupsof_file1 = newignorelist.get(relative1, [])

        duplicates = [file_path1]
        for file_path2 in all_files:
            if file_path2 in already_displayed:
                continue
            if file_path1 == file_path2:
                continue

            relative2 = str(relative_to_main(file_path2))
            if relative2 in false_dupsof_file1 or relative2 in newfalse_dupsof_file1:
                continue

            if testfn(file_path1, file_path2):
                duplicates.append(file_path2)

        if len(duplicates) > 1:
            already_displayed.update(duplicates)
            for dupfile in duplicates:
                print(testname + "   {:<40} {:<200}".format(readable_filesize(file_size(dupfile)), str(dupfile)))
            print("")

            if cliargs.ignore:
                addto_newignorelist(duplicates)


def print_duplicates(all_files):
    all_files = sorted(all_files, key=lambda file_path: str(file_path))

    tests = {
      'name': test_same_name,
      'name_sim': test_same_name_sim,
      'name_prefix': test_same_name_prefix,
      'content': test_same_content
    }

    already_displayed = set()
    for testname, testfn in tests.items():
        if not testname in cliargs.skiptests and (len(cliargs.onlytests) < 1 or testname in cliargs.onlytests):
            if testname == 'fcontent':
                already_displayed = set()
            print_duplicated_byfn(all_files, already_displayed, testname, testfn)

def delete_files(file_list):
    for file in file_list:
        if not Path(file).is_file():
            print("Doesn't exist - " + file)
            continue
        if not (main_path in (Path(file), *Path(file).parents)):
            print("Not in main directory - " + file)
            continue

        print("delete " + file)
        Path(file).unlink()

def addto_newignorelist(duplicates):
    for dupfile1 in duplicates:
        relative1 = str(relative_to_main(dupfile1))
        for dupfile2 in duplicates:
            if dupfile1 != dupfile2:
                relative2 = str(relative_to_main(dupfile2))
                if relative2 not in ignorelist.get(relative1, []) and relative2 not in newignorelist.get(relative1, []):
                    newignorelist.setdefault(relative1, [])
                    newignorelist[relative1].append(relative2)

def load_ignorelist():
    tmp = []
    try:
        if ignorelist_path.exists():
            with ignorelist_path.open() as json_file:
                tmp = json.load(json_file)
    except:
        pass

    # merge ignorelist of different dates
    global ignorelist
    ignorelist = {}
    for ignoreset in tmp:
        for source, targets in ignoreset.items():
            ignorelist.setdefault(source, [])
            ignorelist[source] = list(set(ignorelist.get(source)).union(set(targets)))


def save_ignorelist():
    global newignorelist
    if len(newignorelist) == 0:
        return

    try:
        confirm = input('Are all above movies different ? (y/[n]) ')
    except:
        exit(0)
    if confirm not in ('y', 'Y'):
        print("skipped")
        return

    tmp = []
    if ignorelist_path.exists():
        try:
            with ignorelist_path.open() as json_file:
                tmp = json.load(json_file)
        except:
            pass
    tmp.append(newignorelist)

    with ignorelist_path.open('w') as outfile:
        json.dump(tmp, outfile, indent=4)

    print("Updated ignorelist.json")


def getcliargs():
    parser = argparse.ArgumentParser("duplicates")
    parser.add_argument('directory', nargs='?', default=Path.cwd())
    parser.add_argument('--skiptests', default=[],
                    type=lambda s: [item for item in s.replace(' ', ',').replace(';', ',').split(',')],
                    help='skip tests (possible : name, name_prefix, name_sim, content)')
    parser.add_argument('--onlytests', default=[],
                    type = lambda s: [item for item in s.replace(' ', ',').replace(';', ',').split(',')],
                    help = 'only tests (possible : name, name_prefix, name_sim, content)')
    parser.add_argument('--printnames', default=False, const=True, nargs='?', help='print clean names')
    parser.add_argument('--printtokens', type=int, const=50, nargs='?', help='print most often detected tokens')
    parser.add_argument('--ignore', default=False, const=True, nargs='?', help='Mark current dupplicate list as false positives')

    return parser.parse_args()

def main():
    global cliargs
    global main_path
    global ignorelist_path
    global all_files

    cliargs = getcliargs()
    main_path = cliargs.directory
    ignorelist_path = main_path.joinpath('ignorelist.json')

    delete_files(todelete_files)

    # list files
    all_files = main_path.rglob('*')
    all_files = [file for file in all_files if file.is_file() and file.suffix.lower() not in ignore_extensions]
    for pattern in ignore_patterns:
        pattern = pattern.lower()
        all_files = [file for file in all_files if pattern not in str(file.parent).lower()]

    load_ignorelist()

    if cliargs.printnames:
        print_cleaned_names(all_files)
    elif cliargs.printtokens:
        print_token_stats(all_files)
    else:
        print_duplicates(all_files)
        print('To remove many duplicate files at once, build a list of files with Notepad++ and fill "todelete_files" variable at the top of this script')

    if cliargs.ignore:
        save_ignorelist()

main()
