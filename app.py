from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os
import datetime
import uuid

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Database setup
DB_PATH = "database.db"
UPLOAD_FOLDER = "static/profile_pics"

# Ensure profile pictures folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def create_database():
    """Create SQLite database and tables if they don't exist"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Create users table with additional fields
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT UNIQUE, password TEXT, 
                 age INTEGER DEFAULT NULL, gender TEXT DEFAULT NULL, profile_pic TEXT DEFAULT 'default.png')''')

    # Create assessments table
    c.execute('''CREATE TABLE IF NOT EXISTS assessments 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, mood TEXT, date TEXT,
                 FOREIGN KEY (user_id) REFERENCES users(id))''')

    conn.commit()
    conn.close()

create_database()

def get_profile_picture():
    """Fetch the user's profile picture or return default"""
    if 'user_id' in session:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT profile_pic FROM users WHERE id=?", (session['user_id'],))
        user = c.fetchone()
        conn.close()
        return user[0] if user and user[0] else "default.png"
    return "default.png"  # Always return default if user is not logged in

@app.route('/')
def home():
    profile_pic = get_profile_picture()
    return render_template('home.html', profile_pic=profile_pic)

@app.route('/main-home')
def main_home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    profile_pic = get_profile_picture()
    return render_template('main_home.html', profile_pic=profile_pic)

@app.route('/login', methods=['GET', 'POST'])
def login():
    profile_pic = "default.png"  # Default profile pic for login page

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, profile_pic FROM users WHERE email=? AND password=?", (email, password))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['profile_pic'] = user[1] if user[1] else "default.png"
            flash("You have been logged in successfully!", "success")
            return redirect(url_for('main_home'))
        else:
            flash("Invalid email or password", "danger")
            return render_template('login.html', profile_pic=profile_pic)  # Pass default profile pic

    return render_template('login.html', profile_pic=profile_pic)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    profile_pic = "default.png"  # Default profile pic for signup page

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        try:
            c.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, password))
            conn.commit()
            conn.close()
            flash("Signup successful! Please login.", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("You have already signed up, please log in.", "danger")
            return render_template('signup.html', profile_pic=profile_pic)

    return render_template('signup.html', profile_pic=profile_pic)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    profile_pic = get_profile_picture()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT mood, date FROM assessments WHERE user_id=?", (session['user_id'],))
    assessments = c.fetchall()
    conn.close()

    # Count mood occurrences
    mood_counts = {}
    for mood, _ in assessments:
        mood_counts[mood] = mood_counts.get(mood, 0) + 1

    most_frequent_mood = max(mood_counts, key=mood_counts.get, default="No data")

    return render_template('dashboard.html', profile_pic=profile_pic, assessments=assessments, most_frequent_mood=most_frequent_mood)

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name, age, gender, profile_pic FROM users WHERE id=?", (user_id,))
    user = c.fetchone()
    conn.close()

    # Default values if data is missing
    name = user[0] if user[0] else "Not set"
    age = user[1] if user[1] else "Not set"
    gender = user[2] if user[2] else "Not set"
    profile_pic = user[3] if user[3] else "default.png"

    return render_template('profile.html', profile_pic=profile_pic, name=name, age=age, gender=gender)

@app.route('/upload-profile', methods=['POST'])
def upload_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    if 'profile_pic' not in request.files:
        flash("No file uploaded", "danger")
        return redirect(url_for('profile'))

    file = request.files['profile_pic']
    if file.filename == '':
        flash("No selected file", "danger")
        return redirect(url_for('profile'))

    filename = str(uuid.uuid4()) + "_" + file.filename
    file.save(os.path.join(UPLOAD_FOLDER, filename))

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET profile_pic=? WHERE id=?", (filename, user_id))
    conn.commit()
    conn.close()

    session['profile_pic'] = filename  # Update session variable
    flash("Profile picture updated successfully!", "success")
    return redirect(url_for('profile'))

@app.route('/edit-profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE users SET name=?, age=?, gender=? WHERE id=?", (name, age, gender, user_id))
        conn.commit()
        conn.close()

        flash("Profile updated successfully!", "success")
        return redirect(url_for('profile'))

    return render_template('edit_profile.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route('/submit-assessment', methods=['POST'])
def submit_assessment():
    if 'user_id' not in session:
        return jsonify({"message": "You must be logged in!"}), 401

    user_id = session['user_id']
    mood = request.form.get("q1")
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not mood:
        return jsonify({"message": "Invalid assessment data!"}), 400

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO assessments (user_id, mood, date) VALUES (?, ?, ?)", (user_id, mood, date))
    conn.commit()
    conn.close()

    return jsonify({"message": "Assessment submitted successfully!"})

if __name__ == '__main__':
    app.run(debug=True)
