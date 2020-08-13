"""lol
"""

import string
from .import model
from .import learn
from .model import Word, WordDAO, WType

def process(txt):
    sentence = txt.lower()
    for punct in string.punctuation:
        sentence = sentence.replace(punct, "")
    words = [model.WordDAO.get(keyword) for keyword in sentence.split()]
    return words

def _get_group(words, delimiters=None, authorized=None, restricted=None):
    group = []
    if delimiters is None:
        delimiters = []
    if authorized is None:
        authorized = []
    if restricted is None:
        restricted = []
    for word in words:
        if authorized is None:
            is_delimiter = False
            is_restricted = False
            for type_ in restricted:
                if word.is_type(type_):
                    is_restricted = True
                    break
            for type_ in delimiters:
                if word.is_type(type_):
                    is_delimiter = True
                    break
            if is_delimiter:
                if not is_restricted:
                    group.append(word)
                return group
            else:
                if not is_restricted:
                    group.append(word)
                else:
                    return group
        else:
            is_authorized = False
            is_delimiter = False
            is_restricted = False
            for type_ in authorized:
                if word.is_type(type_):
                    is_authorized = True
                    break
            for type_ in delimiters:
                if word.is_type(type_):
                    is_delimiter = True
                    break
            for type_ in restricted:
                if word.is_type(type_):
                    is_rectrited = True
                    break
            if is_authorized:
                group.append(word)
                if is_delimiter:
                    return group
            else:
                return group
    return group

_VERBAL_GROUP_TYPES = [WType.VERB]
_NOMINAL_GROUP_TYPES = [WType.ADJECTIVE, WType.NOUN]

def regroup(words):
    res = []
    index = 0
    group = []
    groups = []
    while index < len(words):
        word = words[index]
        if word.is_type(WType.ARTICLE):
            authorized = [WType.CONJUNCTION, WType.NOUN, WType.ADJECTIVE]
            restricted = [WType.VERB, WType.ADVERB]
            group = _get_group(words[index+1:], authorized=authorized, restricted=restricted)
            #group = _get_group(words[index+1:], authorized=_NOMINAL_GROUP_TYPES,)# restricted=_NOMINAL_GROUP_TYPES)
            index += len(group)
            group.insert(0, word)
            groups.append((WType.NOUN, group))
        elif word.is_type(WType.NOUN):
            authorized = [WType.CONJUNCTION, WType.NOUN, WType.ADJECTIVE]
            restricted = [WType.VERB, WType.ADVERB]
            group = _get_group(words[index+1:], authorized=authorized, restricted=restricted)
            index += len(group)
            group.insert(0, word)
            groups.append((WType.NOUN, group))
        elif word.is_type(WType.VERB):
            group = _get_group(words[index+1:], authorized=_VERBAL_GROUP_TYPES, restricted=[WType.NOUN])
            index += len(group)
            group.insert(0, word)
            groups.append((WType.VERB, group))
        else:
            groups.append(word)
        index += 1
    return groups

def get_polarity(words):
    "return -1: negativ, 0: neutral and 1: positiv"
    apscore = 0.0
    anscore = 0.0
    cpt = 0
    pscore = 0.0
    nscore = 0.0
    for word in words:
        if word.is_type(learn.SENTIMENT_TYPES):
            apscore += word.apscore
            anscore += word.anscore

            pscore += word.pscore
            nscore += word.nscore
            cpt += 1
    a_score = 0
    _score = 0
    apscore += 1e-6
    anscore += 1e-6
    pscore += 1e-6
    nscore += 1e-6
    if cpt:
        apscore /= cpt
        anscore /= cpt
        a_score = 2*(apscore*anscore)/(apscore+anscore)
        pscore /= cpt
        nscore /= cpt
        _score = 2*(pscore*nscore)/(pscore+nscore)

    delta = 0.1
    if (anscore - delta) > a_score and (anscore - delta) > apscore:
        return -1
    elif (apscore - delta) > a_score and (apscore - delta) > anscore:
        return 1
    elif (a_score - delta) > anscore and (a_score - delta) > apscore:
        return 0
    else:
        if (nscore - delta) > _score and (nscore - delta) > pscore:
            return -1
        elif (pscore - delta) > _score and (pscore - delta) > _score:
            return 1
        else:
            return 0

def get_bases(words):
    last = None
    last2 = None
    bases = [word.get_types() for word in words]
    path = []
    tree = learn.get_tree()
    for index, word in enumerate(words):
        _bases = word.get_types()
        tmp = []
        for _base in _bases:
            if last2 is not None and last is not None:
                key = (last2, last, _base)
            elif last is not None:
                key = (last, _base)
            else:
                key = (_base,)
            tmp.append((tree.get(key,0), key))
        tmp.sort()
        base = tmp[-1][-1][-1]
        last2 = last
        last = base
        path.append(base)
    return path

QWords = ["how", "who", "why", "where", "when", "which", "what"]
RWords = list(QWords)
RWords.extend(["can", "could", "will", "would"])

def get_sentence_type(sentence, words=None):
    if words is None:
        words = tuple(learn.sentence2words(sentence))

    is_request = 0
    is_assert = 0
    is_question = 0
    if words:
        if words[0].word.lower() in QWords or "?" in sentence:
            is_request = 1
            is_question = 1
        elif words[0].is_type(model.WType.VERB):
            is_question = 1
            is_request = 1
        else:
            is_assert = 1
    return is_assert, is_request, is_question

def get_subject_verb_object(sentence, words=None):
    if words is None:
        words = tuple(learn.sentence2words(sentence))
    is_assert, is_request, is_question = get_sentence_type(sentence, words)
    subject = ""
    verb = ""
    _object = ""
    bases = get_bases(words)
    cleaned_words = []
    cleaned_bases = []
    FINAL_TYPES = (WType.VERB, WType.NOUN, WType.PRONOUN, WType.UNKNOWN)
    for _id, word in enumerate(words):
        if bases[_id] in (WType.VERB, WType.NOUN, WType.PRONOUN, WType.UNKNOWN):
            cleaned_bases.append(bases[_id])
            cleaned_words.append(word)
    cleaned_bases = [base for base in bases if base in (WType.VERB, WType.NOUN, WType.PRONOUN, WType.UNKNOWN)]
    final_words = [word for word in cleaned_words if not word.is_type([WType.ARTICLE, WType.ADJECTIVE, WType.ADVERB, WType.CONJUNCTION])]
    grouped_words = regroup(words)
    final_words = []
    for itm in grouped_words:
        if isinstance(itm, (tuple, list)):
            for _itm in reversed(itm[1]):
                if _itm.is_type(FINAL_TYPES):
                    final_words.append(_itm)
                    break
        else:
            final_words.append(itm)
    tmp_verb = ""
    for word in words:
        if word.is_type(WType.VERB):
            tmp_verb = word.word
    words = cleaned_words
    try:
        if words:
            if is_request:
                if is_question:
                    if words[0].word.lower() in QWords:
                        verb = words[1].word
                        subject = words[2].word
                    else:
                        verb = words[0].word
                        subject = words[1].word
                elif words[0].is_type(WType.VERB):
                    verb = words[0].word
                    subject = words[1].word
                else:
                    subject = words[1].word
                    verb = words[0].word
            else:
                verb = words[1].word
                subject = words[0].word
                if len(words) > 2:
                    _object = words[2].word
    except:
        pass
    return subject, verb, _object

def is_human(keyword):
    word = model.WordDAO.get(keyword)
    if word.is_type(WType.PRONOUN):
        return 1
    return 0

def get_infos(sentence):
    words = list(learn.sentence2words(sentence))
    is_assert = 0
    is_negative = 0
    is_neutral = 0
    is_positive = 0
    is_question = 0
    is_request = 0
    _object = ""
    object_is_human = 0
    subject = ""
    subject_is_human = 0
    verb = ""

    _polarity = get_polarity(words)
    if _polarity < 0:
        is_negative = 1
    elif _polarity == 0:
        is_neutral = 1
    else:
        is_positive = 1
    is_assert, is_request, is_question = get_sentence_type(sentence, words)
    subject, verb, _object = get_subject_verb_object(sentence, words)
    object_is_human = is_human(_object)
    subject_is_human = is_human(subject)

    fields = [is_assert, is_negative, is_neutral, is_positive, is_question, is_request,\
              _object, object_is_human, subject, subject_is_human, verb]
    return {
        'is_assert': is_assert,
        'is_negative': is_negative,
        'is_neutral': is_neutral,
        'is_positive': is_positive,
        'is_question': is_question,
        'is_request': is_request,
        'object': _object,
        'object_is_human': object_is_human,
        'subject': subject,
        'subject_is_human': subject_is_human,
        'verb': verb
    }


if __name__ == "__main__":
    txt = "the man wrote a letter."
    words = tuple(learn.sentence2words(txt))
    print(get_sentence_type(txt, words))
    print(get_subject_verb_object(txt, words))