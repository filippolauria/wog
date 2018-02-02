#!/usr/bin/env python3

from argparse import ArgumentParser, ArgumentTypeError
from argparse import RawDescriptionHelpFormatter
from datetime import datetime
from itertools import permutations, product
from threading import Lock, Thread, currentThread
from tqdm import tqdm
import os
import queue
import sys


def banner():
    return("""
 _ _ _     _____
| | | |___|   __|  A simple Wordlist Generator
| | | | . |  |  |   Filippo Lauria (filippolauria@outlook.com)
|_____|___|_____|
                   v1.0
""")


def epilog():
    return("""
Examples
--------
Starting from wordlist.input, creates a wordlist and stores it in
/home/foo/wordlist.output. The wordlist will be generated applying the
all-cases-transformation to wordlist.input and combininig each transformed
word with the others. All the combinations will include the use of a different
separator chosen among these four “, _ . -”. The obtained set will be then
extended using each of the possible year values taken from the range 1980-1999.
The produced wordlist will contain only words with a length
between 8 and 12 characters.

$ ./wog.py -v -a -S , _ . - -Y 1980 1999 -m 8 -M 12 \\
        -o /home/foo/wordlist.output wordlist.input
""")


def istextfile(filepath, blocksize=512):
    int2byte = (lambda x: bytes((x,)))
    _text_characters = (
        b''.join(int2byte(i) for i in range(32, 127)) +
        b'\n\r\t\f\b')

    with open(filepath, 'rb') as fileobj:
        block = fileobj.read(blocksize)
        if b'\x00' in block:
            return False
        elif not block:
            return True

        nontext = block.translate(None, _text_characters)
        return float(len(nontext)) / len(block) <= 0.30

    return None


def outputfile(f):
    if not os.access(os.path.dirname(f), os.W_OK):
        raise ArgumentTypeError(
            '"{}" is not a valid output file path.'.format(f))
    return f


def inputfile(f):
    if (not os.path.isfile(f)) or (not istextfile(f)):
        raise ArgumentTypeError(
            '"{}" is not a valid input file path.'.format(f))
    return f

parser = ArgumentParser(
    prog='WoG', formatter_class=RawDescriptionHelpFormatter,
    description=banner(), epilog=epilog())
parser.add_argument('inputfile', type=inputfile, metavar='input.wordlist',
                    help='the path of the file containing input words')
parser.add_argument('--all-uppercase', action='store_true',
                    help="""if specified, the all-uppercase additive
                    transformation will be applied to all the input words""")
parser.add_argument('--all-lowercase', action='store_true',
                    help="""if specified, the all-lowercase additive
                    transformation will be applied to all the input words""")
parser.add_argument('--first-uppercase', action='store_true',
                    help="""if specified, the first-uppercase additive
                    transformation will be applied to all the input words""")
parser.add_argument('--camelcase', action='store_true',
                    help="""if specified, the camelcase additive
                    transformation will be applied to all the input words""")
parser.add_argument('-a', '--all-possible-cases', action='store_true',
                    help="""if specified, the all-possible-cases
                    additive transformation will be applied
                    to all the input words""")
parser.add_argument('-S', '--separator', nargs='*', type=str, metavar="SEP",
                    help="""the separator(s) applied between
                    (transformed) input words to compose output words""")
parser.add_argument('-Y', '--year', nargs='*', type=str, metavar='YYYY',
                    help="""a year in the form YYYY
                    or a range of years in the form YYYY YYYY""")
parser.add_argument('--begin-with-year', action='store_true',
                    help="""this option is meaningful only if --year is valid.
                    When specified, each of the years in the chosen range
                    is prepended to each of the output words,
                    either in the form YYYY or in the form YY""")
parser.add_argument('--end-with-year', action='store_true',
                    help="""this option is meaningful only if --year is valid.
                    When specified, each of the years in the chosen range
                    is appended to each of the output words,
                    either in the form YYYY or in the form YY""")
parser.add_argument('--splitted-year', action='store_true',
                    help="""this option is meaningful only if --year is valid.
                    When specified, each of the years in the chosen range
                    is splitted in two blocks and in turn prepended
                    and appended to each of the output words""")
parser.add_argument('-A', '--age', nargs='*', type=str, metavar='YY',
                    help="""a age in the form YY
                    or a range of ages in the form YY YY""")
parser.add_argument('--start-with-age', action='store_true',
                    help="""this option is meaningful only if --age is valid.
                    When specified, each of the ages in the chosen range
                    is prepended to each of the output words""")
parser.add_argument('--end-with-age', action='store_true',
                    help="""this option is meaningful only if --age is valid.
                    When specified, each of the ages in the chosen range
                    is appended to each of the output words""")
parser.add_argument('-m', '--min-length', nargs='?', type=int,
                    help="""the minimum number of characters
                    in any output words""")
parser.add_argument('-M', '--max-length', nargs='?', type=int,
                    help="""the maximum number of characters
                    in any output words""")
parser.add_argument('-u', '--uniq', action='store_true',
                    help="""when specified, (almost) all duplicate
                    output words will be removed""")
parser.add_argument('-o', '--output-file', type=outputfile,
                    required=True, metavar='output.wordlist',
                    help='the path of the file containing output words')
parser.add_argument('-v', '--verbose', action='store_true',
                    help='turn on the verbose mode')
args = parser.parse_args()

postparsed = {}
postparsed['verbose'] = args.verbose


def vprint(s):
    if postparsed['verbose']:
        print(s)
    return

vprint('[+] post-parsing arguments..')

postparsed['output-file'] = args.output_file
vprint('[+] the generated wordlist will be saved in "{}"'.format(
    postparsed['output-file']))

if not args.min_length or args.min_length < 0:
    postparsed['min-length'] = False
else:
    postparsed['min-length'] = True
    postparsed['min-length-value'] = args.min_length
    vprint(
        "[+] words with less than {} characters will be not included".format(
            postparsed['min-length-value']))

if not args.max_length or args.max_length < 0:
    postparsed['max-length'] = False
else:
    postparsed['max-length'] = True
    postparsed['max-length-value'] = args.max_length
    vprint(
        "[+] words with more than {} characters will be not included".format(
            postparsed['max-length-value']))
if (postparsed['min-length'] and
        postparsed['max-length'] and
        postparsed['min-length-value'] > postparsed['max-length-value']):
    parser.error(
        "[!] min-length value is greater than max-length value. Swapping..")
    postparsed['min-length-value'] = args.max_length
    postparsed['max-length-value'] = args.min_length

postparsed['input-file'] = args.inputfile
vprint('[+] the input file is "{}"'.format(postparsed['input-file']))

seedlist = []
with open(postparsed['input-file'], 'r') as ifd:
    seedlist = ifd.read().splitlines()

seedlist = list(set(seedlist))
vprint('[+] loaded {} input words'.format(len(seedlist)))

postparsed['all-uppercase'] = args.all_uppercase
postparsed['all-lowercase'] = args.all_lowercase
postparsed['first-uppercase'] = args.first_uppercase
postparsed['all-possible-cases'] = args.all_possible_cases
postparsed['camelcase'] = args.camelcase

if not args.all_possible_cases:
    postparsed['all-possible-cases'] = not (
        postparsed['all-uppercase'] or
        postparsed['all-lowercase'] or
        postparsed['first-uppercase'] or
        postparsed['camelcase']
    )

postparsed['separator'] = ['']
if args.separator:
    postparsed['separator'].extend(list(args.separator))
postparsed['separator'] = list(set(postparsed['separator']))
vprint('[+] considering {} separator(s)'.format(len(postparsed['separator'])))

postparsed['max-word-per-permutation'] = 2

if not args.year:
    postparsed['year'] = False
else:
    postparsed['year'] = True
    yearlist = list(args.year)
    if len(yearlist) > 2:
        parser.error("[-] at most two values for year parameter.")
        sys.exit(-1)
    else:
        for year in yearlist:
            if (len(year) != 4 and not year.isdigit()) or int(year) <= 0:
                parser.error("[-] Invalid year")
                sys.exit(-1)

        yearlist = [int(year) for year in yearlist]

        if len(yearlist) == 2:
            if yearlist[0] == yearlist[1]:
                postparsed['year-range'] = [yearlist[0]]
            else:
                minyear = min(yearlist)
                maxyear = max(yearlist)
                postparsed['year-range'] = range(minyear, maxyear)
                vprint("[+] year values will range from {0} to {1}".format(
                    minyear, maxyear))
        else:
            postparsed['year-range'] = yearlist

if not args.age:
    postparsed['age'] = False
else:
    postparsed['age'] = True
    agelist = list(args.age)
    if len(agelist) > 2:
        parser.error("[-] at most two values for age parameter.")
        sys.exit(-1)
    else:
        for age in agelist:
            if (len(age) != 2 and not age.isdigit()) or int(age) <= 0:
                parser.error("[-] Invalid age")
                sys.exit(-1)

        agelist = [int(age) for age in agelist]

        if len(agelist) == 2:
            if agelist[0] == agelist[1]:
                postparsed['age-range'] = [agelist[0]]
            else:
                minage = min(agelist)
                maxage = max(agelist)+1
                postparsed['age-range'] = range(minage, maxage)
                vprint("[+] age values will range from {0} to {1}".format(
                    minage, maxage))
        else:
            postparsed['age-range'] = agelist

postparsed['begin-with-year'] = args.begin_with_year
postparsed['end-with-year'] = args.end_with_year
postparsed['splitted-year'] = args.splitted_year

if postparsed['year']:
    if not (postparsed['begin-with-year'] or
            postparsed['end-with-year'] or
            postparsed['splitted-year']):
        postparsed['begin-with-year'] = \
            postparsed['end-with-year'] = \
            postparsed['splitted-year'] = True

postparsed['start-with-age'] = args.start_with_age
postparsed['end-with-age'] = args.end_with_age

if postparsed['age']:
    if not (postparsed['start-with-age'] or postparsed['end-with-age']):
        postparsed['start-with-age'] = \
            postparsed['end-with-age'] = True

postparsed['uniq'] = args.uniq
vprint("[+] arguments post-parsing finished.")


stime = datetime.now()
print("[+] {} wordlist generation process has started.".format(
    stime.strftime('%Y-%m-%d %H:%M:%S')))

wordlist = []

if postparsed['all-possible-cases']:
    vprint("[+] applying all-possible-cases transformation..")
    for word in seedlist:
        l = [''.join(t) for t in product(
            *zip(word.lower(), word.upper()))]
        wordlist.extend(l)
else:
    if postparsed['all-uppercase']:
        vprint("[+] applying all-uppercase transformation..")
        wordlist.extend([w.upper() for w in seedlist])
    elif postparsed['all-lowercase']:
        vprint("[+] applying all-lowercase transformation..")
        wordlist.extend([w.lower() for w in seedlist])
    elif postparsed['first-uppercase']:
        vprint("[+] applying first-uppercase transformation..")
        wordlist.extend([w.capitalize() for w in seedlist])
    elif postparsed['camelcase']:
        vprint("[+] applying camelcase transformation..")
        wordlist.extend([w.title() for w in seedlist])

vprint("[+] finished applying transformation(s).")

progresslist = []
progresslist_lock = Lock()

q = queue.Queue()

num_worker_threads = 2 if os.cpu_count() is None else os.cpu_count()
threads = []

progressbar_perm = tqdm(desc='[+] permutations completion')


def make_permutations():
    while True:
        separator = q.get()
        if separator is None:
            q.task_done()
            break
        temp_wordlist = wordlist
        temp_wordlist.append(separator)
        for i in range(2, postparsed['max-word-per-permutation']+1):
            perms = permutations(temp_wordlist, i)
            for p in perms:
                w = ''.join(p)
                if (postparsed['max-length'] and
                        len(w) > postparsed['max-length-value']):
                    continue

                progresslist_lock.acquire()
                progresslist.append(w)
                progresslist_lock.release()
                progressbar_perm.update()
        q.task_done()

for s in postparsed['separator']:
    q.put(s)
for j in range(num_worker_threads):
    q.put(None)

for i in range(num_worker_threads):
    name = "Permutator-{}".format(i)
    t = Thread(target=make_permutations, name=name)
    t.start()
    threads.append(t)

q.join()

for t in threads:
    t.join()

wordlist.extend(progresslist)
wlen = len(wordlist)
progresslist.clear()
vprint("\n[+] current wordlist length: {}".format(wlen))

if postparsed['year']:
    def make_year_tranformation():
        while True:
            i = q.get()
            if i is None:
                q.task_done()
                break

            w = str(wordlist[i])
            progressbar_year.update()

            if (postparsed['max-length'] and
                    len(w) > postparsed['max-length-value']):
                q.task_done()
                continue

            for year in postparsed['year-range']:
                yearstr = str(year)
                yearlow = yearstr[2:4]
                yearthree = yearstr[1:4]

                templist = []

                if postparsed['begin-with-year']:
                    templist.extend([
                        ''.join([yearlow, w]),
                        ''.join([yearstr, w]),
                        ''.join([yearthree, w])
                    ])

                if postparsed['end-with-year']:
                    templist.extend([
                        ''.join([w, yearlow]),
                        ''.join([w, yearstr]),
                        ''.join([w, yearthree])
                    ])

                if postparsed['splitted-year']:
                    yearhigh = yearstr[0:2]
                    templist.append(''.join([yearhigh, w, yearlow]))

                if templist:
                    progresslist_lock.acquire()
                    progresslist.extend(templist)
                    progresslist_lock.release()

            q.task_done()

    progressbar_year = tqdm(
        total=wlen, desc='[+] year transformation completion')

    for i in range(0, wlen):
        q.put(i)

    for j in range(num_worker_threads):
        q.put(None)

    threads.clear()
    for j in range(num_worker_threads):
        name = "Year-Transformer-{}".format(j)
        t = Thread(target=make_year_tranformation, name=name)
        t.start()
        threads.append(t)

    q.join()

    for t in threads:
        t.join()
    progressbar_year.update()

if postparsed['age']:
    def make_age_tranformation():
        while True:
            i = q.get()
            if i is None:
                q.task_done()
                break
            w = str(wordlist[i])
            progressbar_age.update()

            if (postparsed['max-length'] and
                    len(w) > postparsed['max-length-value']):
                q.task_done()
                continue

            for age in postparsed['age-range']:
                agestr = str(age)

                if postparsed['start-with-age']:
                    progresslist_lock.acquire()
                    progresslist.append(''.join([agestr, w]))
                    progresslist_lock.release()

                if postparsed['end-with-age']:
                    progresslist_lock.acquire()
                    progresslist.append(''.join([w, agestr]))
                    progresslist_lock.release()

            q.task_done()

    progressbar_age = tqdm(
        total=wlen, desc='[+] age transformation completion')

    for i in range(0, wlen):
        q.put(i)
    for k in range(num_worker_threads):
        q.put(None)

    threads.clear()
    for j in range(num_worker_threads):
        name = "Age-Transformer-{}".format(j)
        t = Thread(target=make_age_tranformation, name=name)
        t.start()
        threads.append(t)

    q.join()

    for t in threads:
        t.join()
    progressbar_age.update()

if postparsed['uniq']:
    vprint("[+] Removing (almost all) duplicates..")
    wordlist = list(set(wordlist))
    vprint("[+] Removing (almost all) duplicates..")
    progresslist = list(set(progresslist))
    vprint("[+] Finished removing (almost all) duplicates.")

writtenwords = 0
bufsize = 4096
listlen = len(wordlist) + len(progresslist)
ofd = open(postparsed['output-file'], "w", bufsize)

progressbar_outputfile = tqdm(total=listlen, desc="[+] Writing file")
for w in wordlist:
    progressbar_outputfile.update()
    if postparsed['min-length'] and len(w) < postparsed['min-length-value']:
        continue
    ofd.write(str(w)+'\n')
    writtenwords += 1

wordlist.clear()

for w in progresslist:
    progressbar_outputfile.update()
    if postparsed['min-length'] and len(w) < postparsed['min-length-value']:
        continue
    ofd.write(str(w)+'\n')
    writtenwords += 1

progresslist.clear()

ofd.close()

etime = datetime.now()
print("[+] {} wordlist generation process has ended.".format(
    stime.strftime('%Y-%m-%d %H:%M:%S')))
print("[+] {0} words were generated in {1} seconds.".format(
    writtenwords, (etime-stime).total_seconds()))
