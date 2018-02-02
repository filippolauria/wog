WoG v1.0
========
**WoG** is a python tool designed to generate wordlists by applying *some transformations* to a small set of input words.

How does it work?
-----------------
**WoG** starts by reading few words from an input file, then it applies to each word read an *additivite trasformation*, in order to further expand the starting word set. When the expansion of the initial set has been completed, **WoG** starts combininig each word with the others. If some *separators* have been specified, **WoG** repeats the latter process including each of the given *separators*. All the produced combinations are then added to the growing set of words. If a *year* or a *range of years* has been specified, **WoG** can add different *year transformations* to the growing set of words. For example, given the year *ABCD*, possible transformations to the word *foo* could be *fooCD, fooBCD, fooABCD, CDfoo, BCDfoo, ABCDfoo, ABfooCD*. Almost the same goes for *age transformations*.

Installation
------------
**Prerequisites**
- Python 3.5.2
- pip3 (```$ sudo apt-get install python3-pip ```)

**Installation**
```sh
$ git clone https://github.com/filippolauria/wog.git
$ cd wog
$ sudo pip3 install -r requirements.txt
```
WoG arguments
---
```sh
 _ _ _     _____   
| | | |___|   __|  A simple Wordlist Generator
| | | | . |  |  |   Filippo Lauria (filippolauria@outlook.com)
|_____|___|_____|  
                   v1.0
positional arguments:
  input.wordlist        the path of the file containing input words

optional arguments:
  -h, --help            show this help message and exit
  --all-uppercase       if specified, the all-uppercase additive
                        transformation will be applied to all the input words
  --all-lowercase       if specified, the all-lowercase additive
                        transformation will be applied to all the input words
  --first-uppercase     if specified, the first-uppercase additive
                        transformation will be applied to all the input words
  --camelcase           if specified, the camelcase additive transformation
                        will be applied to all the input words
  -a, --all-possible-cases
                        if specified, the all-possible-cases additive
                        transformation will be applied to all the input words
  -S [SEP [SEP ...]], --separator [SEP [SEP ...]]
                        the separator(s) applied between (transformed) input
                        words to compose output words
  -Y [YYYY [YYYY ...]], --year [YYYY [YYYY ...]]
                        a year in the form YYYY or a range of years in the
                        form YYYY YYYY
  --begin-with-year     this option is meaningful only if --year is valid.
                        When specified, each of the years in the chosen range
                        is prepended to each of the output words, either in
                        the form YYYY or in the form YY
  --end-with-year       this option is meaningful only if --year is valid.
                        When specified, each of the years in the chosen range
                        is appended to each of the output words, either in the
                        form YYYY or in the form YY
  --splitted-year       this option is meaningful only if --year is valid.
                        When specified, each of the years in the chosen range
                        is splitted in two blocks and in turn prepended and
                        appended to each of the output words
  -A [YY [YY ...]], --age [YY [YY ...]]
                        a age in the form YY or a range of ages in the form YY
                        YY
  --start-with-age      this option is meaningful only if --age is valid. When
                        specified, each of the ages in the chosen range is
                        prepended to each of the output words
  --end-with-age        this option is meaningful only if --age is valid. When
                        specified, each of the ages in the chosen range is
                        appended to each of the output words
  -m [MIN_LENGTH], --min-length [MIN_LENGTH]
                        the minimum number of characters in any output words
  -M [MAX_LENGTH], --max-length [MAX_LENGTH]
                        the maximum number of characters in any output words
  -u, --uniq            when specified, (almost) all duplicate output words
                        will be removed
  -o output.wordlist, --output-file output.wordlist
                        the path of the file containing output words
  -v, --verbose         turn on the verbose mode
```
Examples
--------
Starting from **wordlist.input**, creates a wordlist and stores it in **/home/foo/wordlist.output**. The wordlist will be generated applying the **all-cases-transformation** to wordlist.input and combininig each transformed word with the others. All the combinations will include the use of a different separator chosen among these four **", _ . -"**. The obtained set will be then extended using *each of the possible year values* taken from the range **1980-1999**. The produced wordlist will contain only words with a length **between 8 and 12 characters**.
```sh
$ ./wog.py -v -a -S , _ . - -Y 1980 1999 -m 8 -M 12 -o /home/foo/wordlist.output wordlist.input
```
