from flask import Flask,render_template,redirect,g
import sqlite3
from database import get_db
import pandas as pd

app=Flask(__name__)

def read_tasks(user_id):
    db = get_db()
    table_name = f"player_{user_id}_tasks"
    df = pd.read_sql_query(f'SELECT * FROM {table_name};', db, index_col='id')
    return df


