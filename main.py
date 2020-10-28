from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import requests, json, re, random, math, pickle
import firebase_admin
from firebase_admin import db

# Initialize Firebase app
firebase_admin.initialize_app(options={'databaseURL': 'https://vitask.firebaseio.com/'})

app = Flask(__name__)

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'canada$God7972#'

ref = db.reference('vitask')

slot_a = {"x":50,"y":0,"price":15,"num":1}
slot_b = {"x":0,"y":50,"price":20,"num":2}
slot_c = {"x":50,"y":100,"price":25,"num":3}
slot_d = {"x":100,"y":50, "price":30,"num":4}

# Homepage
@app.route('/')
def index():
    return render_template('index.html')

# Dashboard
@app.route('/dashboard')
def dashboard():
    # Check if user is loggedin
    if 'loggedin' in session:
        if(session['parking_space']=='A'):
            url = "https://thingspeak.com/channels/1208300/field/1.json"
        elif(session['parking_space']=='B'):
            url = "https://thingspeak.com/channels/1208301/field/1.json"
        elif(session['parking_space']=='C'):
            url = "https://thingspeak.com/channels/1208302/field/1.json"
        else:
            url = "https://thingspeak.com/channels/1208303/field/1.json"
        
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

        for i in range(0,slots):
            empty_slots.append(i+1)

        for i in range(slots,10):
            booked_slots.append(i+1)
        
        return render_template('dashboard.html', username = session['username'], booked_slots = booked_slots, empty_slots = empty_slots, lastupdated = lastupdated, parking_space = session['parking_space'], distance = session['distance'], rate = session['rate'])
    return redirect(url_for('login'))

# Thingspeak write for parking spaces (1-4)
def reservedslots(parking_space):
    temp = ref.child("parkfind").child("reserve").get()
    reservations = []
    if temp is not None:
        for key in temp:
            if(temp[key]["parkingSpace"]==parking_space):
                reservations.append(temp[key])
    total = str(len(reservations))
    # Select the parking space
    if(parking_space=='A'):
        url = "https://api.thingspeak.com/update?api_key=7LHBQ6TZCKKWAYND&field1="+total
    elif(parking_space=='B'):
        url = "https://api.thingspeak.com/update?api_key=YBW96SSU1G299SSS&field1="+total
    elif(parking_space=='C'):
        url = "https://api.thingspeak.com/update?api_key=TOXRGRVZA1I28SIP&field1="+total
    else:
        url = "https://api.thingspeak.com/update?api_key=I2L87XB3VT8P7L8V&field1="+total
    try:
        response = requests.get(url)
    except Exception as e:
        print(e)
    
    
# Distance Function
def calc_distance(x1,y1,x2,y2):
    distance = math.sqrt(((x2-x1)**2)+((y2-y1)**2))
    return distance
    

# Reservation System
@app.route('/reservation')
def reservation():
    # Check if user is loggedin
    if 'loggedin' in session:
        # Check if account exists using Firebase 
        reservations = []
        temp = ref.child("parkfind").child("reserve").get()
        if temp is not None:
            for key in temp:
                if(temp[key]["parkingSpace"]==session['parking_space']):
                    reservations.append(temp[key])
        reservedslots(session['parking_space'])
        return render_template('reservation.html', username = session['username'], reservations = reservations)
    return redirect(url_for('login'))

# Reservation System
@app.route('/submit_reservation', methods=['GET', 'POST'])
def submit_reservation():
    # Check if user is loggedin
    if 'loggedin' in session:
        if request.method == 'POST' and 'carMark' in request.form and 'carNumber' in request.form:
            # Create variables for easy access
            carMark = request.form['carMark']
            carNumber = request.form['carNumber']
            parking_space = session['parking_space']
            username = session['username']
            # Add the reservation
            try: 
                tut_ref = ref.child("parkfind").child("reserve")
                tut_ref.push({
                    'carMark': carMark,
                    'carNumber': carNumber,
                    'parkingSpace': parking_space,
                    'username': username
                })
            except Exception as e:
                print(e)
        return redirect(url_for('reservation'))
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
        # Check if account exists using Firebase
        account = None
        temp = ref.child("parkfind").child("users").get()
        for key in temp:
            if(temp[key]["username"]==username):
                account = temp[key]
        
        # Fetch one record and return result
        # Login successful 
        if(password==account["password"]):
            session['loggedin'] = True
            session['username'] = account["username"]
            # Generate Coordinates
            session['x'] = random.randint(0,100)
            session['y'] = random.randint(0,100)
            
            # Predict parking spot
            filename = 'finalized_model.sav'
            distance_a = calc_distance(session['x'],session['y'],slot_a['x'],slot_a['y'])
            distance_b = calc_distance(session['x'],session['y'],slot_b['x'],slot_b['y'])
            distance_c = calc_distance(session['x'],session['y'],slot_c['x'],slot_c['y'])
            distance_d = calc_distance(session['x'],session['y'],slot_d['x'],slot_d['y'])

            data = [[distance_a,distance_b,distance_c,distance_d,15,20,25,30]]
            classifier = pickle.load(open(filename, 'rb'))
            parking_space = classifier.predict(data)[0]
            all_distance = {'A': round(distance_a), 'B': round(distance_b), 'C': round(distance_c), 'D': round(distance_d)}
            all_rates = {'A': slot_a['price'], 'B': slot_b['price'], 'C': slot_c['price'], 'D': slot_d['price']}
            
            session['parking_space'] = parking_space
            session['distance'] = all_distance[parking_space]
            session['rate'] = all_rates[parking_space]
            
            # Redirect to dashboard
            return redirect(url_for('dashboard'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    # Show the login form with message (if any)
    return render_template('login.html', msg=msg)

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']

        # Check if account exists using Firebase 
        snapshot = "Default"
        temp = ref.child("parkfind").child("users").get()
        for key in temp:
            if(temp[key]["username"]==username):
                snapshot = None
        if snapshot is None:
            account = True
        else:
            account = False
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into users table
            try: 
                tut_ref = ref.child("parkfind").child("users")
                tut_ref.push({
                    'username': username,
                    'password': password
                })
                msg = 'You have successfully registered!'
            except Exception as e:
                print(e)
            
        print(msg)
            
    return render_template('login.html', msg=msg)

# Web Logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('loggedin', None)
    session.pop('x', 0)
    session.pop('y', 0)
    session.pop('parking_space', None)
    session.pop('distance', 0)
    session.pop('rate', 0)
    return redirect(url_for('index'))

# Run the Flask Server
if __name__ == '__main__':
    app.run(debug=True)