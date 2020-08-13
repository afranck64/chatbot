"""
"""
import sys
import os
import glob
import string
import json
import pickle
import itertools

from .model import WType
from . import model
from . import utils

#sys.setrecursionlimit(10000000)

TREE_DUMP_FILE_JSON = "resources/db/tree.json"
TREE_DUMP_FILE_PICKLE = "resources/db/tree.list.pkl"

SENTENCES_DIR = "resources/training/sentences"

POS_DIR = "resources/training/parts_of_speach"
SENTIWORDNET_FILE = "resources/training/sentiwordnet/SentiWordNet.txt"
SENTIMENTS_LABELLED_DIR = "resources/training/sentiment_labelled_sentences"
OPINION_LEXICON_DIR = "resources/training/opinion_lexicon"
E_LEMMA_FILE = "resources/training/e_lemma/e_lemma.txt"
MULTI_DIR = os.path.join(POS_DIR, "MULTI")

MINIMUM_TRAIN_OCCURENCIES = 3

FILE_TYPES = {WType.ADVERB:"adverbs", WType.ADJECTIVE:"adjectives",\
             WType.VERB:"verbs", WType.NOUN:"nouns", \
             WType.PREPOSITION:"others/prepositions", WType.CONJUNCTION:"others/conjunctions",\
             WType.PRONOUN:"others/pronouns", WType.DETERMINER:"others/determiners",\
             WType.EXCLAMATION:"others/exclamations", WType.ARTICLE:"articles"}

MULTI_TYPES = {"pronoun": WType.PRONOUN, "noun": WType.NOUN, "adverb": WType.ADVERB,\
              "adjective": WType.ADJECTIVE, "interjection": WType.EXCLAMATION,\
              "verb": WType.VERB, "auxiliary verb": WType.VERB, "past": WType.VERB,\
              "conjunction": WType.CONJUNCTION, "preposition": WType.PREPOSITION,\
              "definite article": WType.ARTICLE, "indefinite article": WType.ARTICLE,\
              "number": None, "predeterminer": None, "past participle": WType.VERB,\
              "idiom": None}

SENTIMENTLESS_TYPES = [WType.PRONOUN, WType.PREPOSITION, WType.CONJUNCTION, WType.ARTICLE]
SENTIMENT_TYPES = [WType.NOUN, WType.ADVERB, WType.ADJECTIVE, WType.EXCLAMATION, WType.VERB]

MAX_DEPTH = -1
MAX_SENTENCE_LENGTH = MAX_DEPTH

USE_JSON = False

HEAD = "head"
BODY = "body"
TAIL = "tail"
TREE_HEAD = "head"
TREE_BODY = "body"
TREE_TAIL = "tail"
TREE_CONFIG = "_config"

MARKOV_MEMORY_SIZE = 4

def _process_multi_types():
    """Assign to each word a part of speach based on the multi db."""
    model.WordDAO.set_auto_commit(False)
    filenames = glob.glob(os.path.join(MULTI_DIR, "*.txt"))
    for filename in filenames:
        for keyword, reftypes in utils.get_multiple_data(filename):
            for reftype in reftypes:
                wtype = MULTI_TYPES[reftype]
                if wtype is not None:
                    word = model.WordDAO.get(keyword)
                    word.set_type(MULTI_TYPES[reftype], True)
                    model.WordDAO.save(word)
    model.WordDAO.set_auto_commit(True)


def process_types():
    """Assign to each word a part of speach."""
    model.WordDAO.set_auto_commit(False)
    for wtype, sub_dir in FILE_TYPES.items():
        search_dir = os.path.join(POS_DIR, sub_dir, "*.txt")
        filenames = glob.glob(search_dir)
        #print search_dir, filenames
        for filename in filenames:
            for keyword in utils.get_words(filename):
                word = model.WordDAO.get(keyword)
                word.set_type(wtype, True)
                model.WordDAO.save(word)
    _process_multi_types()
    model.WordDAO.set_auto_commit(True)

def process_sentiwords():
    """Assign to each word an absolute pos/neg score,
    based on the sentiwordnet database."""
    items = utils.get_sentiwordnet_data(SENTIWORDNET_FILE)
    model.WordDAO.set_auto_commit(False)
    for keyword, apscore, anscore in items:
        word = model.WordDAO.get(keyword)
        word.apscore = apscore
        word.anscore = anscore
        model.WordDAO.save(word)
    model.WordDAO.set_auto_commit(True)

def process_sentiments():
    """Assign to each word an relative pos/neg score,
    based on the computed score of human labelled sentences."""
    model.WordDAO.set_auto_commit(False)
    #Reset scores and scores
    for word in model.WordDAO.get_all():
        word.pscore = 0.0
        word.nscore = 0.0
        word.nb_pos = 0
        word.nb_neg = 0
        model.WordDAO.save(word)

    filenames = glob.glob(os.path.join(SENTIMENTS_LABELLED_DIR, "*.txt"))
    for filename in filenames:
        for keywords, sentiment in utils.get_sentiment_labelled_data(filename):
            words = [model.WordDAO.get(keyword) for keyword in keywords]
            for word in words:
                sentimentless_type = False
                for w_type in SENTIMENTLESS_TYPES:
                    if word.is_type(w_type):
                        sentimentless_type = True
                        break
                if not sentimentless_type:
                    if sentiment == 1:
                        word.pscore += 1.0
                        word.nb_pos += 1
                        model.WordDAO.save(word)
                    else:
                        word.nscore +=1.0
                        word.nb_neg += 1
                        model.WordDAO.save(word)
    for word in model.WordDAO.get_all():
        nb_trains = (word.nb_pos + word.nb_neg)
        if nb_trains > MINIMUM_TRAIN_OCCURENCIES:
            word.pscore /= nb_trains
            word.nscore /= nb_trains
            model.WordDAO.save(word)
        else:
            word.pscore = 0.0
            word.nscore = 0.0
            word.nb_pos = 0
            word.nb_neg = 0
            model.WordDAO.save(word)
    model.WordDAO.set_auto_commit(True)

def process_opinions():
    """Assign to each word an absolute pos/neg score,
    based on the opinion-lexicon."""
    model.WordDAO.set_auto_commit(False)
    filenames = glob.glob(os.path.join(OPINION_LEXICON_DIR, "positive", "*.txt"))
    for filename in filenames:
        for keyword in utils.get_words(filename):
            word = model.WordDAO.get(keyword)
            word.apscore = 1
            model.WordDAO.save(word)

    filenames = glob.glob(os.path.join(OPINION_LEXICON_DIR, "negative", "*.txt"))
    for filename in filenames:
        for keyword in utils.get_words(filename):
            word = model.WordDAO.get(str(keyword))
            word.anscore = 1
            model.WordDAO.save(word)
    model.WordDAO.set_auto_commit(True)

def _clone_attributes(groups):
    """Clones attributes of known words to their synonymes, and transformations."""
    model.WordDAO.set_auto_commit(False)
    cpt = 0
    total = 0
    for group in groups:
        keyword = None
        word = None
        for key in group:
            if model.WordDAO.getID(key) is not None:
                tmp_word = model.WordDAO.get(key)
                if tmp_word.type:
                    keyword = key
                    word = tmp_word
                    break
        if not keyword:
            #TODO None of the words in the group are registred in the DB,
            #how to manage them?
            cpt += 1
            continue
        word = model.WordDAO.get(keyword)
        #print keyword, word.__dict__
        for key in group:
            if key != keyword:
                if model.WordDAO.getID(key) is None:
                    word_clone = word.clone(keyword)
                    model.WordDAO.save(word_clone)
                else:
                    old_word = model.WordDAO.get(key)
                    if not old_word.type:
                        word_clone = word.clone(keyword)
                        model.WordDAO.save(word_clone)
                    #TODO What to do with worlds having a type already set?
        total += 1
    #print "Skipped %d / %d" % (cpt, total)
    model.WordDAO.set_auto_commit(True)

def clone_attributes():
    """clone attributes of close words / synonyms which aren't yet into
    the database, or which lacks informations."""
    _clone_attributes(utils.get_sentiwordnet_groups(SENTIWORDNET_FILE))
    _clone_attributes(utils.get_e_lemma_groups(E_LEMMA_FILE))


def sentence2words(sentence):
    """convert a sentence to a list of <Word>"""
    data = sentence
    for punc in string.punctuation:
        data = data.replace(punc, " ")
    lst = data.split(" ")
    while "" in lst:
        lst.remove("")
    words = (model.WordDAO.get(keyword) for keyword in lst)
    return words


def _sentence2bases(sentence):
    """convert a sentence in a corresponding list of bases"""
    return tuple(word.get_types() for word in sentence2words(sentence))

def _bases2nodes(bases, root):
    for index in range(len(bases)):
        params = ()
        id_min = max(index-MARKOV_MEMORY_SIZE, 0)
        id_max = min(index+1, len(bases))
        params = itertools.product(*bases[id_min:id_max])
        for key in params:
            if key:
                if index <= MARKOV_MEMORY_SIZE:
                    root[TREE_HEAD][key] = root[TREE_HEAD].get(key, 0) + 1
                elif index < len(bases)-MARKOV_MEMORY_SIZE:
                    root[TREE_BODY][key] = root[TREE_BODY].get(key, 0) + 1
                else:
                    root[TREE_TAIL][key] = root[TREE_TAIL].get(key, 0) + 1

        """
        if last2 and last:
            for _last2 in last2:
                for _last in last:
                    key = (_last2, _last, wtype)
                    params.append(key)
        elif not last2 and last:
            for _last in last:
                key = (_last, wtype)
                params.append(key)
        else:
            key = (wtype,)
            params.append(key)
        for key in params:
            if index < 3:
                root[HEAD][key] = root[HEAD].get(key, 0) + 1
            elif index < len(bases)-3:
                root[BODY][key] = root[BODY].get(key, 0) + 1
            else:
                root[TAIL][key] = root[TAIL].get(key, 0) + 1
        last2 = last
        last = base
        lasts.insert(0, base)
        lasts.pop()
        index += 1
        """


def _bases2tree(bases_groups, root):
    for bases in bases_groups:
        _bases2nodes(bases, root)
    return root

def _sentences2tree(sentences):
    """Build a knowledge <PNode> tree from the list<str> of sentences."""
    root = dict(head=dict(), body=dict(), tail=dict())
    for sentence in sentences:
        bases = _sentence2bases(sentence)
        _bases2tree(bases, root)
    return root

def _words2tree(words_lists):
    """Build a knowledge <PNode> tree from the list of word's lists: list<str>"""
    root = dict(head=dict(), body=dict(), tail=dict())
    for words in words_lists:
        bases = tuple(word.get_types() for word in words)
        _bases2tree(bases, root)
    return root


def _get_bases_groups():
    filenames = glob.glob(os.path.join(SENTENCES_DIR, "*.txt"))
    for filename in filenames:
        for sentence in utils.get_sentences(filename):
            words = tuple(sentence2words(sentence))
            if MAX_SENTENCE_LENGTH > 0 and len(words) > MAX_SENTENCE_LENGTH:
                continue
            bases = tuple(word.get_types() for word in words)
            yield bases

    #return
    filenames = glob.glob(os.path.join(SENTIMENTS_LABELLED_DIR, "*.txt"))
    for filename in filenames:
        for keywords, _ in utils.get_sentiment_labelled_data(filename):
            if MAX_SENTENCE_LENGTH > 0 and len(keywords) > MAX_SENTENCE_LENGTH:
                continue
            words = (model.WordDAO.get(keyword) for keyword in keywords)
            bases = tuple(word.get_types() for word in words)
            yield bases


def _normalize_node_scores(tree):
    return
    """
    count = sum(node.score for node in tree.get_nodes()) * 1.0
    for node in tree.get_nodes():
        node.score /= count
    for node in tree.get_nodes():
        _normalize_node_scores(node)
    """

def build_tree():
    #root = dict(head=dict(), body=dict(), tail=dict(), config=)
    root = {TREE_HEAD: dict(), TREE_BODY: dict(), TREE_TAIL: dict(), TREE_CONFIG: dict()}
    root[TREE_CONFIG]["memory_size"] = MARKOV_MEMORY_SIZE
    _bases2tree(_get_bases_groups(), root)
    #_normalize_node_scores(root)
    return root

def get_tree():
    tree = None
    try:
        if USE_JSON:
            with open(TREE_DUMP_FILE_JSON, "rb") as open_f:
                tree = json.load(open_f, cls=model.CJSONDecoder)
        else:
            with open(TREE_DUMP_FILE_PICKLE, "rb") as open_f:
                tree = pickle.load(open_f)
        if tree[TREE_CONFIG]["memory_size"] != MARKOV_MEMORY_SIZE:
            raise ValueError("Different tree memory and config memory.")

    except Exception as err:
        #print err.message
        tree = None

    if not tree:
        tree = build_tree()
        if USE_JSON:
            with open(TREE_DUMP_FILE_JSON, "wb") as open_f:
                json.dump(tree, open_f, cls=model.CJSONEncoder)
        else:
            with open(TREE_DUMP_FILE_PICKLE, "wb") as open_f:
                pickle.dump(tree, open_f, protocol=-1)
    return tree

def match_sentence(sentence):
    words = sentence2words(sentence)
    root = get_tree()
    bases = [word.get_types() for word in words]
    params = []
    index = 0
    last2 = []
    last = []
    path = []
    #print bases
    best_matches = []
    CORRECT_DEPTH = 2

    for index in range(len(bases)):
        if bases[index] == (0,):
            bases[index] = range(1, model.NB_WTYPES)
        if index > MARKOV_MEMORY_SIZE - CORRECT_DEPTH:
            for _id in range(1, CORRECT_DEPTH):
                bases[index - MARKOV_MEMORY_SIZE + _id] = [path[index - MARKOV_MEMORY_SIZE + _id]]
        params = ()
        id_min = max(index-MARKOV_MEMORY_SIZE, 0)
        id_max = min(index+1, len(bases))
        params = tuple(itertools.product(*bases[id_min:id_max]))

        tmp = []
        for key in params:
            if key:
                if index < MARKOV_MEMORY_SIZE:
                    score = root[TREE_HEAD].get(key, 0)
                elif index < len(bases)-MARKOV_MEMORY_SIZE:
                    score = root[TREE_BODY].get(key, 0)
                else:
                    score = root[TREE_TAIL].get(key, 0)
                tmp.append((score, key))
        tmp.sort()
        best = tmp[-1][-1]
        best_matches.append(tmp[-1])
        score = tmp[-1][0]

        for id_path in range(1, CORRECT_DEPTH):
            if len(best) > id_path:
                id_2 = len(best) - id_path - 1
                if path[-id_path] != best[id_2] and best[id_2] != WType.UNKNOWN and score > best_matches[-id_path][0]:
                    path[-id_path] = best[id_2]

        """
        if len(path) > 0:
            if len(best) == 3:
                if path[-1] != best[1] and best[1] != WType.UNKNOWN:
                    path[-1] = best[1]
                if path[-2] != best[0] and best[0] != WType.UNKNOWN:
                    path[-2] = best[0]
            elif len(best) == 2 and best[0] != WType.UNKNOWN:
                if path[-1] != best[0]:
                    path[-1] = best[0]
        """
        #print path, tmp[-1]
        path.append(tmp[-1][-1][-1])
        #print best
    #print best_matches
    return path

def learn():
    """Learn from the gathered informations."""
    process_types()
    process_sentiwords()
    process_opinions()
    process_sentiments()

    clone_attributes()


def test():
    filenames = glob.glob(os.path.join(SENTENCES_DIR, "*.txt"))
    cpt = 0
    for filename in filenames:
        for sentence in utils.get_sentences(filename):
            seq = match_sentence(sentence)
            print(seq, repr(sentence.strip()))
            cpt += 1
            if cpt >= 10:
                break

    #return

if __name__ == "__main__":
    #learn()
    #txt = "Do not love another until you have walked for two moons in his moccasins"
    #txt = "xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx xxxx"
    #txt = "what the hell is this fucking and shat shdhdd!!?"
    #txt = "Iteratively returns the first n Fibonacci numbers, starting from 0 "
    test()