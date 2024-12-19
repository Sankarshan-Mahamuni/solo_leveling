from database import get_db
from flask import session,app
from rankings import get_rankings
from datetime import datetime, timedelta

def get_player_info():
    user_id=session.get("user_id")
    if not user_id:
        return "user not logged in"
    db=get_db()
    cur=db.cursor()
    cur.execute("SELECT Name,Xp,Level from players where id=?",(user_id,))
    data=cur.fetchone()
    Name=data[0]
    Xp=data[1]
    Level=data[2]
    player_info_list=[Name,Xp,Level]
    cur.close()
    return player_info_list

def get_incompleted_tasks():
    user_id=session.get("user_id")
    if not user_id:
        return "user not logged in"
    table_name=f"player_{user_id}_tasks"
    db=get_db()
    cur=db.cursor()
    cur.execute(f"select title from {table_name} where completed=0")
    data=cur.fetchall()
    print(data)
    cur.close()
    incompleted_tasks_list=[task[0] for task in data]
    return incompleted_tasks_list

def get_player_of_week():
    df = get_rankings()
    df = df.iloc[0]
    df = df.to_dict()
    values = [str(v) for v in df.values()]
    return '> '.join(values)

def get_top_players():
    df=get_rankings()
    df=df.iloc[0:3]['Name']
    df=df.to_dict()
    values=[str(v) for v in df.values()]
    return values

def get_today_plan(date):
    user_id = session.get("user_id")
    if not user_id:
        return "user not logged in"
    table_name = f"player_{user_id}_plans"
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute(f"SELECT title FROM {table_name} WHERE date = ?", (date,))
        data = cur.fetchall()
        tasks_list = [task[0] for task in data]
        if not tasks_list:
            tasks_list = ["No plans for today!"]
        print(tasks_list)
    except:
        tasks_list = ["skills plan not yet set !"]
    cur.close()
    return tasks_list
