"""
"""
import sys
import os
import glob
import string
import json
import cPickle as pickle

from model import WType
import model
import utils

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

def _extend_node(node, bases, index=0):
    """extends the <Pnode> node with <Wtype> groups in bases."""
    if MAX_DEPTH > 0 and index > MAX_DEPTH:
        return
    if len(bases) > index:
        base = bases[index]
        for wtype in base:
            found = False
            for _node in node.nodes:
                if _node.type == wtype:
                    _node.score += 1
                    found = True
                    break
            if not found:
                node.nodes.append(model.PNode(wtype, 1))
    else:
        node.is_leaf = True
    for _node in node.get_nodes():
        _extend_node(_node, bases, index+1)

def _bases2nodes(bases, root, index=0, last=None, last2=None):
    params = []
    while len(bases) > index:
        base = bases[index]
        params = []
        for wtype in base:
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
        index += 1


def _bases2tree(bases_groups, root):
    for bases in bases_groups:
        _bases2nodes(bases, root)
    return root

def _sentences2tree(sentences):
    """Build a knowledge <PNode> tree from the list<str> of sentences."""
    root = model.PNode()
    for sentence in sentences:
        bases = _sentence2bases(sentence)
        _bases2tree(bases, root)
    return root

def _words2tree(words_lists):
    """Build a knowledge <PNode> tree from the list of word's lists: list<str>"""
    root = model.PNode()
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
    print bases
    while index < len(bases):
        base = bases[index]
        real_base = base
        if base == (0,):
            base = range(1, model.NB_WTYPES)
        params = []
        for wtype in base:
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
        tmp = []
        for key in params:
            if index < 3:
                score = root[HEAD].get(key, 0)
            elif index < len(bases)-3:
                score = root[BODY].get(key, 0)
            else:
                score = root[TAIL].get(key, 0)
            tmp.append((score, key))
        tmp.sort()
        #print tmp
        path.append(tmp[-1][-1][-1])
        last2 = last
        last = real_base #[path[-1]]
        index += 1
    return path

def learn():
    """Learn from the gathered informations."""
    process_types()
    process_sentiwords()
    process_opinions()
    process_sentiments()

    clone_attributes()



if __name__ == "__main__":
    #learn()
    """
    tree = get_tree()
    #for k, v in tree.items():
    #    print k, v.nodes.keys(), v.score
    for v in tree.get_nodes():
        #print len(v.nodes.values())
        #print v.type, v.score, len(v.nodes)
        for _v in v.get_nodes():
            print v.type, _v.type, _v.score, len(_v.get_nodes())
        print "\n\n"
    #print tree.nodes.keys()
    for v in tree.get_nodes():
        print v.type, v.score
    #print tree
    #print res
    #myword = model.WordDAO.get("porn")
    #print word
    #print model.WordDAO.get("the").get_types()
    #print model.WordDAO.get("this").get_types()
    

    tree = get_tree()
    for k in sorted(tree):
        print k, tree[k]
    """
    txt = "Do not love another until you have walked for two moons in his moccasins"
    res = match_sentence(txt)
    print "\n", res
    print dir(get_tree())