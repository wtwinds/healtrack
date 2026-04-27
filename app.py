from flask import Flask, render_template, request, redirect, flash, session, jsonify
from pymongo import MongoClient
import os
import random

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# ================= DATABASE =================
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)

db = client['healtrack']
users = db['users']
doctors_col = db['doctors']
appointments = db['appointments']

# ================= LOGIN =================
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = users.find_one({"email": email})

        if user and user['password'] == password:
            session['user'] = user['name']
            return redirect('/dashboard')
        else:
            flash("Invalid Email or Password", "danger")

    return render_template("login.html")


# ================= REGISTER =================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash("Passwords do not match", "warning")
            return redirect('/register')

        if users.find_one({"email": email}):
            flash("User already exists!", "warning")
            return redirect('/register')

        users.insert_one({
            "name": name,
            "email": email,
            "password": password
        })

        session['user'] = name
        flash("Registration Successful", "success")
        return redirect('/dashboard')

    return render_template("register.html")


# ================= DASHBOARD =================
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')
    return render_template("dashboard.html")


# ================= GET DOCTORS =================
@app.route('/get-doctors/<department>')
def get_doctors(department):
    data = doctors_col.find({"department": department})
    doctor_list = [doc['name'] for doc in data]
    return jsonify(doctor_list)


# ================= BOOK APPOINTMENT =================
@app.route('/book', methods=['GET', 'POST'])
def book():
    if 'user' not in session:
        return redirect('/')

    if request.method == 'POST':
        department = request.form.get('department')
        doctor = request.form.get('doctor')
        date = request.form.get('date')
        time = request.form.get('time')

        # 🔥 Booking ID generate
        booking_id = "OPD" + str(random.randint(10000, 99999))

        # Save in DB
        appointments.insert_one({
            "user": session['user'],
            "department": department,
            "doctor": doctor,
            "date": date,
            "time": time,
            "booking_id": booking_id
        })

        # 🔥 SHOW CONFIRM PAGE (NO redirect)
        return render_template("confirm.html",
                               booking_id=booking_id,
                               doctor=doctor,
                               department=department,
                               date=date,
                               time=time)

    departments = doctors_col.distinct("department")
    return render_template("book.html", departments=departments)

# ================= MY APPOINTMENTS =================
@app.route('/my-appointments')
def my_appointments():
    if 'user' not in session:
        return redirect('/')

    data = appointments.find({"user": session['user']})
    return render_template("appointments.html", data=data)


# ================= LOGOUT =================
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)