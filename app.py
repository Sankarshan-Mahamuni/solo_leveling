from flask import Flask, render_template, request, redirect, url_for, g, session, jsonify, abort,flash,get_flashed_messages
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
# from database import get_db
from tasks import read_tasks
from rankings import get_rankings
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from datetime import datetime, timedelta


app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

DATABASE = 'data/app.db'
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE, timeout=10)  # Set timeout to 10 seconds
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with open('schema.sql', 'r') as f:
            db.executescript(f.read())

# players task table creation___________________________________________________________________

def create_user_tasks_table(user_id):
    db = get_db()
    cur = db.cursor()
    table_name = f"player_{user_id}_tasks"
    
    cur.execute(f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY NOT NULL,
            title TEXT NOT NULL,
            exp INTEGER NOT NULL DEFAULT 20,
            completed BOOLEAN DEFAULT 0
        )
    ''')
    
    tasks = [
        ('25 PUSH-UPS', 20),
        ('10 DIAMOND PUSH-UPS', 20),
        ('10 PULL-UPS', 25),
        ('10 CHIN-UPS', 25),
        ('SPRINT (running 2-rounds )', 20),
        ('READ 2 PAGES OF SELF-HELP BOOKS', 25),
        ('MEDITATION 15 MINUTES', 25)
    ]
    
    cur.executemany(f'INSERT INTO {table_name} (title, exp) VALUES (?, ?)', tasks)
    db.commit()
    cur.close()
    #-----------------------------------------------------------------------------------------------



def user_exists(username):
    db = get_db()
    user = db.execute('SELECT * FROM players WHERE Name = ?', (username,)).fetchone()
    return user is not None

def create_player(data):
    if not user_exists(data['Name']):
        db = get_db()
        db.execute('''
            INSERT INTO players (Name, Age, Height, Weight, Email, Level, Xp, Strength_level, Strength_points, Intelligence_level, Intelligence_points, Imotional_control, Meditation_points)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['Name'], data['Age'], data['Height'], data['Weight'], data['Email'],
            data['Level'], data['Xp'], data['Strength_level'], data['Strength_points'],
            data['Intelligence_level'], data['Intelligence_points'], data['Imotional_control'], data['Meditation_points']
        ))
        db.commit()
        return True
    return False


def get_username(user_id):
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT Name FROM players WHERE id = ?', (user_id,))
    result = cur.fetchone()
    if result:
        return result[0]
    else:
        return None

def player_id(username):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id FROM players WHERE Name = ?", (username,))
    result = cur.fetchone()
    cur.close()
    
    if result:
        return result[0]  
    return "username not found"

def check_user_in_db(username):
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE Username = ?', (username,)).fetchone()
    return user is not None

def add_user_to_db(username, password):
    db = get_db()
    db.execute('INSERT INTO users (Username, Password) VALUES (?, ?)', (username, password))
    db.commit()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if request.form.get('button') == 'Accept':
            return redirect(url_for('login'))
        else:
            return redirect(url_for('setprofile'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if check_user_in_db(username):
            db = get_db()
            user = db.execute('SELECT * FROM users WHERE Username = ?', (username,)).fetchone()
            if check_password_hash(user['Password'], password):
                user_id = player_id(username)
                session['user_id'] = user_id
                session['username'] =get_username(user_id)
                return redirect(url_for('profileview', user_id=user_id))
            else:
                return abort(401, description="Invalid password.")
        else:
            return redirect(url_for('setprofile', username=username))
    return render_template('login.html')

@app.route('/setprofile', methods=['GET', 'POST'])
def setprofile():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['username']
        age = request.form['age']
        height = request.form['height']
        weight = request.form['weight']
        email = request.form['email']
        Level = 0
        Xp = 0
        Strength_level = 0
        Strength_points = 0
        Intelligence_level = 0
        Intelligence_points = 0
        Imotional_control = 0
        Meditation_points = 0

        hashed_password = generate_password_hash(password)

        player_data = {
            'Name': name, 'Age': age, 'Height': height, 'Weight': weight, 'Email': email,
            'Level': Level, 'Xp': Xp, 'Strength_level': Strength_level, 'Strength_points': Strength_points,
            'Intelligence_level': Intelligence_level, 'Intelligence_points': Intelligence_points,
            'Imotional_control': Imotional_control, 'Meditation_points': Meditation_points
        }

        if create_player(player_data):
            add_user_to_db(username, hashed_password)
            user_id = player_id(username)
            session['user_id'] = user_id

            create_user_tasks_table(user_id)

            return redirect(url_for('profileview', user_id=user_id))
        else:
            error = "Username already exists."
            return render_template('setprofile.html', error=error)
    return render_template('setprofile.html')

@app.route('/profileview/<user_id>')
def profileview(user_id):
    
    db = get_db()
    user = db.execute('SELECT * FROM players WHERE id = ?', (user_id,)).fetchone()
    if user:
        profile_data = dict(user)
        return render_template('profileview.html', user_id=user_id, profile_data=profile_data)
    else:
        return abort(404, description="Profile not found.")




#TASK HANDLING >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

@app.route("/tasks_manager", methods=['GET', 'POST'])
def tasks_manager():
    user_id = session.get('user_id')
    df = read_tasks(user_id)
    tasks = df.to_dict(orient='index')
    if not user_id:
        return jsonify({'error': 'User not logged in'}), 401

    if request.method == "POST":
        data = request.get_json()
        task_ids = data.get('task_ids', [])
        update_task_completion(user_id, task_ids)
        return jsonify({'success': True})
    else:
        return render_template('tasks.html', tasks=tasks, user_id=user_id)

def update_task_completion(user_id, task_ids):
    try:
        table_name = f"player_{user_id}_tasks"

        print(f"Updating tasks: task_ids={task_ids}, table_name={table_name}")

        db = get_db()
        cur = db.cursor()

        for task_id in task_ids:
            cur.execute(f'UPDATE {table_name} SET completed = ? WHERE title = ?', (True, task_id))
            flash(f"Task {task_id} completed !! ")

        exp_points = 0
        strength_points = 0
        intelligence_points = 0
        meditation_points = 0
        for task_id in task_ids:
            cur.execute(f'SELECT exp FROM {table_name} WHERE title = ?', (task_id,))
            row = cur.fetchone()
            if row:
                task_exp, = row
                exp_points += task_exp

                cur.execute(f'SELECT title FROM {table_name} WHERE title = ?', (task_id,))
                row = cur.fetchone()
                if row:
                    task_name = row[0]
                    if task_name in ['25 PUSH-UPS', '10 DIAMOND PUSH-UPS', '10 PULL-UPS', '10 CHIN-UPS']:
                        strength_points += task_exp
                    elif task_name == 'READ 2 PAGES OF SELF-HELP BOOKS':
                        intelligence_points += task_exp
                    elif task_name == 'MEDITATION 15 MINUTES':
                        meditation_points += task_exp
                else:
                    print(f"Error: No task found with id {task_id} and name")
            else:
                print(f"Error: No task found with id {task_id} and exp")

        cur.execute('UPDATE players SET Xp = Xp + ?, Strength_points = Strength_points + ?, Intelligence_points = Intelligence_points + ?, Meditation_points = Meditation_points + ? WHERE id = ?', (exp_points, strength_points, intelligence_points, meditation_points, user_id))
        db.commit()

        cur.execute('SELECT Level, Xp FROM players WHERE id = ?', (user_id,))
        row = cur.fetchone()
        if row:
            player_level, player_xp = row
            if player_xp >= player_level * 160:
                new_level = player_level + 1
                cur.execute('UPDATE players SET Level = ? WHERE id = ?', (new_level, user_id))
                db.commit()
                flash(f" level {new_level} unlocked !! ")
        else:
            print(f"Error: No player found with id {user_id}")

        cur.close()
    except Exception as e:
        print(f"Error updating tasks: {e}")
        return jsonify({'error': f'Failed to update task completion: {str(e)}'}), 500

    return jsonify({'success': True})



#setting____________________________________________________________________
from settings import add_task,delete_task

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    user_id = session.get('user_id')
    df = read_tasks(user_id)
    tasks = df.to_dict(orient='index')
    
    if user_id:
        print("Fetched user ID successfully")
    
    if request.method == 'POST':
        new_task = request.form.get("new_task")
        if new_task:
            add_task(new_task)
            flash("Task update successful")
            return redirect(url_for('settings'))
        data=request.get_json()
        task_titles=data.get('task_titles',[])
        delete_task(task_titles)
        flash("Task deleted successful")
        return jsonify({'success': True})
    else:
        return render_template("settings.html", user_id=user_id,tasks=tasks)



# apk shedular>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

def delete_all_rows(table_name):
    db = get_db()
    cur = db.cursor()
    cur.execute(f'DELETE FROM {table_name}')
    db.commit()
    cur.close()

def reset_autoincrement(table_name):
    db = get_db()
    cur = db.cursor()
    cur.execute(f'DELETE FROM sqlite_sequence WHERE name=?', (table_name,))
    db.commit()
    cur.close()

def set_default(table_name):
    db = get_db()
    cur=db.cursor()
    cur.execute(f"UPDATE {table_name} SET completed=0")
    db.commit()
    cur.close()
    flash(f"tasks are now reset for {table_name}")

# delete_all_rows(table_name)
# reset_autoincrement(table_name)


def reset_all_tasks():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id FROM players")
    player_ids = cur.fetchall()
    cur.close()

    for player_id in player_ids:
        table_name = f"player_{player_id[0]}_tasks"
        set_default(table_name)
        
@app.route("/admin",methods=['GET','POST'])
def admin():
    user_id=session.get('user_id')
    if not user_id:
        return "player not logged in !"
    table_name=f"player_{user_id}_plans"
    if request.method=='POST':
        button_id=request.form.get("call-python-btn")
        if button_id=="reset-all-tasks":
            reset_all_tasks()
    return render_template("admin.html")

@app.route("/reset_tasks", methods=["POST"])
def reset_tasks():
    user_id=session.get('user_id')
    if not user_id:
        return "player not logged in !"
    table_name=f"player_{user_id}_plans"
    if request.method=='POST':
        button_id=request.form.get("call-python-btn")
        if button_id=="plan-table":
                delete_all_rows(table_name)
                reset_autoincrement(table_name)
                flash("plans table deleted successfully !")
        return redirect(url_for('admin'))



scheduler = BackgroundScheduler()
scheduler.add_job(func=reset_all_tasks, trigger='cron', hour=0, minute=0)
scheduler.start()

@app.route('/leaderboard')
def leaderboard():
    rankings = get_rankings().to_dict(orient='index')
    return render_template('leaderboard.html', rankings=rankings)

#....................................................................................................

@app.route('/userguide')
def userguide():
    return render_template('userguide.html')


@app.route('/logout', methods=['POST'])
def logout():
    # Clear the session or perform any necessary logout operations
    session.clear()
    return redirect(url_for('index'))

@app.route('/logout')
def logout_page():
    return render_template('logout.html')


#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
from create_plan import create_users_plan_table

@app.template_filter('strftime')
def format_datetime(value, format='%d-%m-%Y'):
    """Format a date time to (Default): d-m-Y"""
    if isinstance(value, datetime):
        return value.strftime(format)
    return value

def convert_to_todo_list(plan_text):
    lines = plan_text.split('\n')
    plan_items = {}
    current_day = None

    for line in lines:
        line = line.strip()
        if line.startswith("Day"):
            current_day = line.split(':')[0]
            plan_items[current_day] = []
        elif current_day and line:
            plan_items[current_day].append(line)

    return plan_items

@app.route('/create_plan', methods=['GET', 'POST'])
def create_plan():
    user_id = session.get('user_id')
    if not user_id:
        return "Player not logged in!"
    if request.method == 'POST':
        plan_text = request.form['plan_text']
        data = convert_to_todo_list(plan_text)
        start_date = datetime.now()
        tasks = []
        for i, (day, topics) in enumerate(data.items()):
            date = (start_date + timedelta(days=i)).strftime('%d-%m-%y')
            for topic in topics:
                tasks.append((day, topic, date))
        create_users_plan_table(user_id)
        table_name = f"player_{user_id}_plans"
        db = get_db()
        cur = db.cursor()
        cur.executemany(f'INSERT INTO {table_name} (day, title, date) VALUES (?, ?, ?)', tasks)
        db.commit()
        cur.close()
        return redirect(url_for('view_plan'))
    return render_template('create_plan.html')

@app.route('/view_plan')
def view_plan():
    user_id = session.get('user_id')
    table_name = f"player_{user_id}_plans"
    db = get_db()
    cur = db.cursor()
    tasks = cur.execute(f'SELECT * FROM {table_name}').fetchall()
    cur.close()
    tasks_by_day = {}
    for task in tasks:
        day = task['day']
        if day not in tasks_by_day:
            tasks_by_day[day] = []
        tasks_by_day[day].append(task)
    return render_template('view_plan.html', tasks_by_day=tasks_by_day)

@app.route('/complete_task', methods=['POST'])
def complete_task():
    task_id = request.form['task_id']
    user_id = session.get('user_id')
    table_name = f"player_{user_id}_plans"
    conn = get_db()
    conn.execute(f'UPDATE {table_name} SET completed = 1 WHERE id = ?', (task_id,))
    flash(" Congratulations! you are one step closer to your goal 🫡 ")
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})




#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>




from homedata import get_player_info,get_incompleted_tasks,get_player_of_week,get_top_players,get_today_plan
@app.route('/home')
def home():
    date=datetime.now().strftime('%d-%m-%y')
    # Mock data for the demonstration
    player_info=get_player_info()
    username = player_info[0]
    total_xp = player_info[1]
    current_level = player_info[2]
    recent_activities = ["Completed Task 1", "Gained Strength Level", "Completed Daily Quest"]
    incompleted_tasks = get_incompleted_tasks()
    upcoming_tasks=incompleted_tasks
    # upcoming_tasks = ["Task 2", "Task 3", "Task 4"]
    achievements =get_today_plan(date)
    daily_quest = "Complete your daily tasks"
    random_quote = "My aim is continuous improvement, not any final destination."
    player_of_the_week =get_player_of_week()
    top_players = get_top_players()

    return render_template('home.html', username=username, total_xp=total_xp, current_level=current_level,
                           recent_activities=recent_activities, upcoming_tasks=upcoming_tasks, achievements=achievements,
                           daily_quest=daily_quest, random_quote=random_quote, player_of_the_week=player_of_the_week,
                           top_players=top_players,date=date)


if __name__ == '__main__':
    atexit.register(lambda: scheduler.shutdown())
    app.run(debug=True)
