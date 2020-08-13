"""This module contains data models for the basic chatbot
"""

import json
from . import utils
from . import db

WType = utils.enum(UNKNOWN=0, NOUN=1, VERB=2, ADJECTIVE=3, ADVERB=4, PRONOUN=5,
                   PREPOSITION=6, CONJUNCTION=7, DETERMINER=8, EXCLAMATION=9,
                   ARTICLE=10)
NB_WTYPES = 11


class PNode(object):
    def __init__(self, wtype=WType.UNKNOWN, score=0, is_leaf=False, nodes=None):
        self.score = score
        self.type = wtype
        self.is_leaf = is_leaf
        if nodes is None:
            nodes = []
        self.nodes = nodes

    def get_nodes(self):
        #return tuple(node for node in self.nodes if node)
        return self.nodes

class CJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, PNode):
            return {
                "_type": "model.PNode",
                "value": obj.__dict__
            }
        return super(CJSONEncoder, self).default(obj)

class CJSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        if "_type" not in obj:
            return obj
        _type = obj["_type"]
        if _type == "model.PNode":
            fields = obj["value"]
            return PNode(fields["type"], fields["score"], fields["is_leaf"], fields["nodes"])
        return obj


class Word(object):
    """A Word a represent anything word that could appear in a sentence."""
    def __init__(self, keyword, pscore=-1, nscore=-1, _type=0, apscore=0, anscore=0,
                 nb_pos=0, nb_neg=0, _id=None):
        #keyword = keyword.lower()
        self.word = keyword
        self.type = _type
        self.pscore = pscore
        self.nscore = nscore
        self.id = _id
        self.apscore = apscore
        self.anscore = anscore
        self.nb_pos = nb_pos
        self.nb_neg = nb_neg

    def is_type(self, wtype):
        """Get the type value for <wtype>"""
        if isinstance(wtype, (list, tuple)):
            for _type in wtype:
                if (self.type >> _type) & 1:
                    return True
            return False
        else:
            return (self.type >> wtype) & 1

    def set_type(self, wtype, value):
        """Set the type value <wtype> of this word."""
        if value:
            self.type |= (1 << wtype)
        else:
            self.type &= (0 << wtype)

    def get_types(self):
        """Return all types of this word."""
        res = tuple(_id for _id in range(NB_WTYPES) if self.is_type(_id))
        return res or (0,)

    def save(self):
        """Persistently save this word."""
        WordDAO.save(self)

    def clone(self, keyword):
        """Clone the parameters of the actual word to a new word with <keyword>."""
        _id = WordDAO.getID(keyword)
        return Word(keyword=keyword, pscore=self.pscore, nscore=self.nscore, _type=self.type,
                    apscore=self.apscore, anscore=self.anscore, nb_pos=self.nb_pos,
                    nb_neg=self.nb_neg, _id=_id)
    def __str__(self):
        return "<%s - %d>" % (self.word, self.type)

    def __repr__(self):
        return "<%s - %d>" % (self.word, self.type)


class WordDAO(object):
    """Word data access object manager."""

    @classmethod
    def get_all(cls):
        """Returns all words present in the DB."""
        sql = "select word, pscore, nscore, type, apscore, anscore, nb_pos, nb_neg, id "\
                " from %s" % db.DBManager.table
        res = db.DBManager.execute(sql)
        for row in res:
            yield Word(*row)

    @classmethod
    def get(cls, keyword=None):
        """Loads the word from the database."""
        #keyword = keyword.lower()
        sql = "select pscore, nscore, type, apscore, anscore, nb_pos, nb_neg, id "\
                " from %s where word=:word" % db.DBManager.table
        res = db.DBManager.execute(sql, {"word":keyword.lower()})
        if res:
            itm = res[0]
            return Word(keyword, *itm)
        else:
            return Word(keyword)


    @classmethod
    def getID(cls, keyword=None):
        """Returns an valid ID if <keyword> is in the database and None else."""
        #keyword = keyword.lower()
        sql = "select id from %s where word=:word" % db.DBManager.table
        res = db.DBManager.execute(sql, {"word": keyword.lower()})
        if res:
            return int(res[0][0])
        else:
            return None

    @classmethod
    def save(cls, word):
        """Saves a word to the database."""
        if word.id is not None:
            cls.update(word)
            return
        else:
            sql = "insert into %s (word, pscore, nscore, type, apscore, anscore, nb_pos, nb_neg) "\
                    "values (:word, :pscore, :nscore, :type, :apscore, :anscore, :nb_pos, :nb_neg)"\
                     % db.DBManager.table
            fields = dict(word.__dict__)
            fields["word"] = fields["word"].lower()
            db.DBManager.execute(sql, fields)

    @classmethod
    def delete(cls, word):
        """Deletes the corresponding word in the database."""
        sql = "delete from %s where id=:id" % db.DBManager.table
        if word.id:
            db.DBManager.execute(sql, (word.__dict__))

    @classmethod
    def update(cls, word):
        """Update the corresponding word in the database."""
        if word.id is None:
            cls.save(word)
            return
        else:
            if word.id <= 0:
                return
            sql = "update %s set word=:word, pscore=:pscore, nscore=:nscore, type=:type, "\
                    "apscore=:apscore, anscore=:anscore, nb_pos=:nb_pos, nb_neg=:nb_neg "\
                    " where id=:id" % db.DBManager.table
            fields = dict(word.__dict__)
            fields["word"] = fields["word"].lower()
            db.DBManager.execute(sql, fields)

    @classmethod
    def set_auto_commit(cls, value=True):
        """Enable or disable auto commit after each query to speed up batch queries."""
        db.DBManager.set_auto_commit(value)
    
    @classmethod
    def is_populated(cls):
        sql = f"select count(*) from {db.DBManager.table}"
        return db.DBManager.execute(sql)[0][0] > 0


def bench():
    """lol"""
    lst = []
    for key in utils.get_base_words():
        lst.append(WordDAO.get(key))
    #print len(lst)

if __name__ == "__main__":
    """
    for word in WordDAO.get_all():
        if word.type > 0:
            print word.word
    """
    p = PNode(0, 2)
    q = PNode(0, 6)
    print(p[0], q[0], q[2])
    p[0] = 2
