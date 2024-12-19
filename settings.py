from database import get_db
from flask import session,jsonify
def add_task(new_task):
    db=get_db()
    cur=db.cursor()
    user_id= session.get('user_id')
    if user_id:
        table_name=f"player_{user_id}_tasks"
        cur.execute(f"INSERT INTO {table_name} (title) values (?) ;",(new_task,))
        db.commit()
        cur.close()
    return True

def delete_task(task_titles):
    db=get_db()
    cur=db.cursor()
    user_id= session.get('user_id')
    table_name=f"player_{user_id}_tasks"
    for task_title in task_titles:
        cur.execute(f"DELETE FROM {table_name} WHERE title=?;",(task_title,))
        db.commit()
    cur.close()
    return jsonify({'success': True})

    

    
