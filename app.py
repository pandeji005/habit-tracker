from flask import Flask, render_template, request, jsonify,session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, timedelta

app = Flask(__name__)
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.secret_key = "supersecretkey"

# MySQL configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///habit.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class HabitLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)


class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)


class Mood(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    mood = db.Column(db.String(10), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login_page')
def login_page():
    return render_template('login.html')

@app.route('/register_page')
def register_page():
    return render_template('register.html')


@app.route('/add_habit', methods=['POST'])
def add_habit():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401
    
    
    data = request.get_json()

    name = data.get('name')
    user_id = session['user_id']

    new_habit = Habit(name=name, user_id=user_id)

    db.session.add(new_habit)
    db.session.commit()

    return jsonify({'message': 'Habit added successfully'}), 201


@app.route('/get_habits', methods=['GET'])
def get_habits():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401

    user_id = session['user_id']
    habits = Habit.query.filter_by(user_id=user_id).all()

    

    return jsonify([
        {"id": h.id, "name": h.name}
        for h in habits
    ]) 

    


@app.route('/complete_habit', methods=['POST'])
def complete_habit():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401
    data = request.get_json()

    habit_id = data.get('habit_id')
    user_id = session['user_id']
    today = date.today()
    
    if not habit_id:
        return jsonify({'message': 'Habit ID required'}), 400
    # Check if habit belongs to user (VERY IMPORTANT)
    habit = Habit.query.filter_by(id=habit_id, user_id=user_id).first()

    if not habit:
        return jsonify({'message': 'Invalid habit'}), 403

    # Check if already completed today
    existing = HabitLog.query.filter_by(habit_id=habit_id, date=today).first()

    if existing:
        return jsonify({'message': 'Already marked for today'}), 400

    # Add new log
    new_log = HabitLog(habit_id=habit_id, date=today)

    db.session.add(new_log)
    db.session.commit()

    return jsonify({'message': 'Habit marked as complete'}), 201



@app.route('/streak/<int:habit_id>', methods=['GET'])
def get_streak(habit_id):
    logs = HabitLog.query.filter_by(habit_id=habit_id).order_by(HabitLog.date.desc()).all()

    streak = 0
    current_date = date.today()

    for log in logs:
        if log.date == current_date:
            streak += 1
            current_date = current_date - timedelta(days=1)
        else:
            break

    return jsonify({'streak': streak})

@app.route('/add_mood', methods=['POST'])
def add_mood():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401
    data = request.get_json()

    user_id = session['user_id']
    mood = data.get('mood')
    today = date.today()

    # prevent multiple entries per day
    existing = Mood.query.filter_by(user_id=user_id, date=today).first()

    if existing:
        existing.mood = mood
    else:
        new_mood = Mood(user_id=user_id, mood=mood, date=today)
        db.session.add(new_mood)

    db.session.commit()

    return jsonify({'message': 'Mood recorded'}), 200


@app.route('/mood_history', methods=['GET'])
def mood_history():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401

    user_id = session['user_id']
    moods = Mood.query.filter_by(user_id=user_id).order_by(Mood.date.desc()).all()

    return jsonify([
        {
            "date": str(m.date),
            "mood": m.mood
        }
        for m in moods
    ])


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'message': 'Username and password required'}), 400
    
    

    

    # Check if user already exists
    existing_user = User.query.filter_by(username=username).first()

    if existing_user:
        return jsonify({'message': 'User already exists'}), 409
    # Hash the password
    hashed_password = generate_password_hash(password)
    # Create new user
    new_user = User(username=username, password=hashed_password)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'message': 'Username and password required'}), 400

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password, password):
        session['user_id'] = user.id  # Store user ID in session
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'message': 'Invalid username or password'}), 401
    

@app.route('/check_session')
def check_session():
    return jsonify({'user_id': session.get('user_id')})
    
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/logout', methods=['GET'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out successfully'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)