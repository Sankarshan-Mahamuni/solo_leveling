from database import get_db
from flask import session


def create_users_plan_table(user_id):
    if not user_id:
        return "User not logged in!"
    
    table_name = f"player_{user_id}_plans"
    db = get_db()
    cur = db.cursor()
    cur.execute(f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY NOT NULL,
            day TEXT NOT NULL,
            title TEXT NOT NULL,
            completed BOOLEAN DEFAULT 0,
            date TEXT NOT NULL
        )
    ''')
    db.commit()
    cur.close()
    return True