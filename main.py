from flask import Flask, render_template, request, redirect, url_for, session
from flaskext.mysql import MySQL
from datetime import datetime
import requests, json, re, bcrypt

app = Flask(__name__)

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'canada$God7972#'

# Enter your database connection details below
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD	'] = ''
app.config['MYSQL_DATABASE_DB'] = 'parking'

# Intialize MySQL
mysql = MySQL(autocommit=True)
mysql.init_app(app)

#Homepage
@app.route('/')
def index():
    return render_template('index.html')

#Dashboard
@app.route('/dashboard')
def dashboard():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        cursor = mysql.get_db().cursor()
        cursor.execute('SELECT * FROM users WHERE ID = %s', [session['id']])
        account = cursor.fetchone()
        url = "https://thingspeak.com/channels/1163641/field/1.json"
        try:
            response = requests.get(url)
            data = json.loads(response.text)
            record = data['feeds'][-1]['field1']
            if record is None:
                record = 0
        except:
            record = 0
        slots = int(record)
        lastupdated_nonformatted = datetime.now()
        # dd/mm/YY H:M:S
        lastupdated = lastupdated_nonformatted.strftime("%d/%m/%Y %H:%M:%S")
        booked_slots = []
        empty_slots = []
        # print(f"slots are {slots}")
        for i in range(0,slots):
            empty_slots.append(i+1)
        # print(booked_slots)
        for i in range(slots,10):
            booked_slots.append(i+1)
        # print(empty_slots)
        return render_template('dashboard.html', username = session['username'], booked_slots = booked_slots, empty_slots = empty_slots, lastupdated = lastupdated)
    return redirect(url_for('login'))

#Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.get_db().cursor()
        cursor.execute('SELECT * FROM users WHERE Username = %s', (username))
        # Fetch one record and return result
        account = cursor.fetchone()
        # print(account)
        # Login successful 
        if bcrypt.checkpw(password.encode('utf-8'), account[2].encode('utf-8')):
            session['loggedin'] = True
            session['id'] = account[0]
            session['username'] = account[1]

            # Redirect to dashboard
            return redirect(url_for('dashboard'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    # Show the login form with message (if any)
    return render_template('login.html', msg=msg)

#Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']

        # Check if account exists using MySQL
        cursor = mysql.get_db().cursor()
        cursor.execute('SELECT * FROM users WHERE Username = %s', (username))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into users table
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute('INSERT INTO users VALUES (NULL, %s, %s)', (username, hashed_password))
            msg = 'You have successfully registered!'
            
    return render_template('login.html', msg=msg)

#run the Flask Server
if __name__ == '__main__':
    app.run(debug=True)