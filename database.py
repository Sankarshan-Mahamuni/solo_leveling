import sqlite3
from flask import g

# DATABASE = 'data/app.db'


# def get_db():
#     if 'db' not in g:
#         g.db = sqlite3.connect(DATABASE)
#         g.db.row_factory = sqlite3.Row
#     return g.db

DATABASE = 'data/app.db'
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE, timeout=10)  # Set timeout to 10 seconds
        g.db.row_factory = sqlite3.Row
    return g.db