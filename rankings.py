from database import get_db
import pandas as pd

def get_rankings():
    db=get_db()
    cur=db.cursor()
    df=pd.read_sql_query("SELECT NAME,LEVEL,XP FROM PLAYERS ORDER BY LEVEL desc",db)
    df.index+=1
    df.index.name='RANK'
    return df