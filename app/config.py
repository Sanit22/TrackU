import os


basedir = os.path.abspath(os.path.dirname(__file__))


class LocalDevelopment:
    ENV = 'development'
    DEBUG = True
    TESTING = True
    SECRET_KEY = 'nadfas$%3@=_dsnisvnsv!'
    SQL_DB_DIR = os.path.join(basedir, 'database')
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(SQL_DB_DIR, "trackuDb.sqlite3")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    

