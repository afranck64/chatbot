# -- coding: utf-8 --
import sqlite3
import os
import sys
import pathlib

from . import utils

DB_PATH = pathlib.Path(__file__).parent.parent.joinpath("resources/db/db.sqlite3")
os.makedirs(DB_PATH.parent, exist_ok=True)
print(DB_PATH)

DB_SQL_SCHEMA = """
CREATE TABLE IF NOT EXISTS words
(id INTEGER PRIMARY KEY, word TEXT COLLATE NOCASE, pscore REAL, nscore REAL, type INT);"""

DB_SQL_SCHEMA = """
CREATE TABLE IF NOT EXISTS words
(id INTEGER PRIMARY KEY, word TEXT not null unique, pscore REAL not null, nscore REAL not null,
type INT not null, apscore REAL not null, anscore REAL not null, nb_pos INT not null,
nb_neg INT not null)"""
# word: the word of interest
# pscore: the relative positive score generated for the word
# nscore: the relative negative score generated for the word
# type: the word type at a bit level based on model.WType
# apscore: the absolute positive score of the word
# anscore: the absolute negative score of the word
# nb_pos: the number of positive matches during training
# nb_neg: the number of negative matches during training
DB_SQL_INDEX_WORD = "CREATE INDEX IF NOT EXISTS word_index on words(word COLLATE NOCASE);"

def icompare(text1, text2):
    return (u"%s" % text1).lower() == (u"%s" % text2).lower()



class DBManager(object):
    sql_schemas = (DB_SQL_SCHEMA,)
    sql_indexes = (DB_SQL_INDEX_WORD,)
    filename = DB_PATH
    conn = None
    table = "Words"
    sql_get = ""
    sql_update = ""
    sql_delete = ""
    sql_save = ""
    _auto_commit = True

    @classmethod
    def open(cls):
        if cls.conn:
            return
        cls.conn = sqlite3.connect(cls.filename)
        cls.conn.create_function("icompare", 2, icompare)

    @classmethod
    def getConn(cls):
        if cls.conn is None:
            cls.open()
        return cls.conn

    @classmethod
    def close(cls):
        if cls.conn:
            cls.conn.commit()
            cls.conn.close()
            cls.conn = None

    @classmethod
    def init_db(cls):
        """Init the database if it doesn't exist yet."""
        if not os.path.exists(cls.filename):
            cursor = cls.getConn().cursor()
            for sql in cls.sql_schemas:
                cursor.execute(sql)
            for sql in cls.sql_indexes:
                cursor.execute(sql)
            cursor.close()
            if cls._auto_commit:
                cls.getConn().commit()

    @classmethod
    def force_init_db(cls):
        """Force the initialisation of the database and overwrite it."""
        if os.path.exists(cls.filename):
            os.remove(cls.filename)
        cls.init_db()

    @classmethod
    def execute(cls, sql, data=None):
        res = tuple()
        try:
            conn = cls.getConn()
            cursor = conn.cursor()
            if data is None:
                res = tuple(cursor.execute(sql))
            else:
                res = tuple(cursor.execute(sql, data))
            cursor.close()
            if cls._auto_commit:
                conn.commit()
        except (sqlite3.IntegrityError, sqlite3.InternalError):
            print("Error on: ", sql, data)
            pass
        return res

    @classmethod
    def executemany(cls, sql, data=None):
        res = []
        conn = cls.getConn()
        cursor = conn.cursor()
        if data is not None:
            for data_row in data:
                try:
                    res.append(cursor.execute(sql, data_row))
                except (sqlite3.IntegrityError, sqlite3.InternalError):
                    print("Error on: ", sql, data)
                    pass
        else:
            try:
                res.append(cursor.execute(sql))
            except (sqlite3.IntegrityError, sqlite3.InternalError):
                print("Error on: ", sql, data)
                pass
        cursor.close()
        if cls._auto_commit:
            conn.commit()
        return res

    @classmethod
    def populate_db(cls, data):
        """Populate the database with items in data."""
        query = "insert into %s (word, pscore, nscore, type, apscore, anscore, nb_pos, nb_neg) "\
            "values(?, ?, ?, ?, ?, ?, ?, ?);" % cls.table
        data = [(itm.lower(), -1, -1, 0, 0, 0, 0, 0) for itm in data]
        #cls.execute(query2 % datad[0])
        #print list(data)s
        cls.executemany(query, data)


    @classmethod
    def set_auto_commit(cls, value=True):
        cls._auto_commit = value
        if value:
            cls.getConn().commit()


DBManager.init_db()
if __name__ == "__main__":
    #DBManager.populate_db(utils.get_base_words())
    print(list(utils.get_base_words()))
    #result = DBManager.execute("select * from words")
    #print len(result)
    print("END!")
