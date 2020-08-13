"""This module contains help functions or other modules."""

import codecs
import string

WORDS_PATH = "resources/training/google-10000-english.txt"


def enum(*sequential, **named):
    """Create an Enum type"""
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)

def get_words(filename=WORDS_PATH):
    """Returns the words in the file,
    assuming there is one word per line."""
    with codecs.open(filename, "r", "utf8") as open_f:
        for line in open_f.readlines():
            yield line.replace("\n", "").replace("\r", "")

def get_sentiwordnet_data(filename):
    """Returns <keyword, apscore, anscore> list from sentiwordnet."""
    with codecs.open(filename, "r", "utf8") as open_f:
        for line in open_f.readlines():
            if line and line[0] == "#":
                continue
            lst = line.split()
            if len(lst) < 4:
                continue
            apscore = lst[2]
            anscore = lst[3]
            for itm in lst[4:]:
                if "#" in itm:
                    yield itm.split("#")[0].strip(), apscore, anscore
                else:
                    break

def get_sentiwordnet_groups(filename):
    """Return <keyword, variation1, ..., variationn> list from sentiwordnet."""
    with codecs.open(filename, "r", "utf8") as open_f:
        for line in open_f.readlines():
            if line and line[0] == "#":
                continue
            lst = line.split()
            if len(lst) < 4:
                continue
            variations = []
            for itm in lst[4:]:
                if "#" in itm:
                    variations.append(itm.split("#")[0].strip())
                else:
                    break
            if len(variations) > 1:
                yield variations


def get_e_lemma_groups(filename):
    """Return <keyword, (variation1,...)> from e_lemma"""
    with codecs.open(filename, "r", "utf8") as open_f:
        for line in open_f.readlines():
            if line and line[0] == ";":
                continue
            data = line.split("->")
            data = [itm.strip() for itm in data]
            if len(data) == 2:
                keyword = data[0]
                variations = [itm.strip() for itm in data[1].split(",")]
                variations.insert(0, keyword)
                yield variations

def get_sentiment_labelled_data(filename):
    """Return <(keyword1, ..., keywordN), sentiment> list,
    where sentiment is 0 for negative and 1 for positive."""
    with codecs.open(filename, "r", "utf8") as open_f:
        for line in open_f.readlines():
            for punctuation_s in string.punctuation:
                line = line.replace(punctuation_s, "")
            data = line.split()
            sentiment = None
            try:
                sentiment = int(data[-1])
            except (ValueError, TypeError) as err:
                pass
            if sentiment is not None:
                yield data[:-1], int(data[-1])

def get_multiple_data(filename):
    """Return <keyword, (type1, ..., typen)> list of words from a multiple file.
    ROW-format:
    KEYWORD+TABULATION+ID+TABULATION+(TYPE1,...,TYPEN)"""
    with codecs.open(filename, "r", "utf8") as open_f:
        lst = open_f.readlines()
        for row in lst:
            row = row.replace("\n", "").replace("\r", "")
            row_data = row.split("\t")
            keyword, types = row_data[0], row_data[-1][1:-1].split(",")
            yield (keyword, types)

def get_sentences(filename):
    with codecs.open(filename, "r", encoding="utf8") as open_f:
        for line in open_f.readlines():
            line = line.replace("\n", "")
            if line:
                lst = line.split(u" ")
                yield u" ".join(lst[1:])

get_base_words = get_words

if __name__ == "__main__":
    #print list(get_base_words())
    import learn
    res = get_e_lemma_groups(learn.E_LEMMA_FILE)
    print (res)
    print (list(res))