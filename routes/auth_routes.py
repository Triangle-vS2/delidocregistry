from flask import Blueprint, request, flash, redirect, url_for, render_template, flash
from services.token_flow import verify_user
from services.sql_flow import test_db_connection
from services.auth_service import authenticate_user
import requests, mysql.connector, json

auth = Blueprint('auth', __name__)

@auth.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    role        = request.form.get('role')
    username    = request.form.get('username')
    password    = request.form.get('password')

    clock_in_code   = request.form.get('clock_in_code')
    delivery_code   = request.form.get('delivery_code')
    mfa_code        = request.form.get('mfa_code')

    # Basic inline validation
    has_error = False
    if not role:
        flash("Role is required", "error")
        has_error = True
    if not username:
        flash("Username is required", "error")
        has_error = True
    if not password:
        flash("Password is required", "error")
        has_error = True

    #  Role-specific validation
    if role == 'member' and not clock_in_code:
        flash("Clock-in code is required for members", "error")
        has_error = True
    if role == 'supplier' and not delivery_code:
        flash("Delivery code is required for suppliers", "error")
        has_error = True
    if role == 'manager' and not mfa_code:
        flash("MFA code is required for managers", "error")
        has_error = True

    if has_error:
        return render_template('login.html')
    
    # --- MySQL Authentication ---
    user = authenticate_user(username, password)
    if not user:
        flash("Invalid credentials", "error")
        return render_template('login.html')
    
    # Optional: check user.role
    # if user.role != role:

    # --- role-specific logic ---
    if role == 'member':
        # e.g. record clock-in, validate format
        if not validate_clock_in(clock_in_code):
            flash("Login failed!", "failed")
            return render_template('login.html')
        
    elif role == 'supplier':
        # External API
        if not validate_delivery_code(delivery_code):
            flash("Login failed!", "failed")
            return render_template('login.html')
        
    elif role == 'manager':
        # MFA bypass
        return redirect(url_for('dashboard'))
    
    flash(('error', 'unkown'))
    return render_template('login.html')

def authenticate_user(username, password):
    # Simulate DB lookup
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='Mysql_1'
    )
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
    user = cursor.fetchone()
    cursor.close(); conn.close()
    return user
    return {"username": username, "role": "member"}  # Mocked user  

def validate_clock_in(code):
        return bool(code)

EXTERNAL_API_URL = "https://jsonplaceholder.typicode.com/posts"
def validate_delivery_code(code):
    resp = requests.post(EXTERNAL_API_URL, json={"code": code})
    return resp.status_code == 200
    return True