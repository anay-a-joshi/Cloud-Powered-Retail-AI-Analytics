# Here is the code for the Flask application that will be used to interact with the database on Azure Services 
# and generate the dashboard and do/perform other tasks.

# Let's start by importing the required libraries and modules in Python.
from flask import Flask, render_template, request, redirect, url_for, send_file, session
from flask_sqlalchemy import SQLAlchemy
from collections import Counter
import re
import csv
import os
import pyodbc

# Database connection details
server_name = 'retail-server-project.database.windows.net'
username_db = 'anayjoshi'
db_password = 'cloudFall2024'
db_name = 'retail_db'

# Initialize the Flask application
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.getcwd(), 'users.db')}"
app.config['SECRET_KEY'] = 'dummy_key'
db = SQLAlchemy(app)

# Here is the User class that will be used to create the User table in the database.
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    firstname = db.Column(db.String(80))
    lastname = db.Column(db.String(80))
    email = db.Column(db.String(120), unique=True, nullable=False)

# Create the User table in the database
with app.app_context():
    db.create_all()

# Function to query the database for customer trends
def query_customer_trends(query, data=None, attempt=1):
    try:
        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server_name};DATABASE={db_name};UID={username_db};PWD={db_password}"
        )
        cursor = conn.cursor()
        print(f"Executing Query: {query}")
        print(f"With Parameters: {data}")
        if data:
            cursor.execute(query, data)
        else:
            cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    except Exception as error:
        print(f"Error: {error}")
        if attempt <= 3:
            return query_customer_trends(query, data, attempt + 1)
        else:
            return "error"

# Function to get search data from the database
def get_search_data(query, data=None, attempt=1):
    try:
        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server_name};DATABASE={db_name};UID={username_db};PWD={db_password}"
        )
        cursor = conn.cursor()

        if data:
            cursor.execute(query, data)
        else:
            cursor.execute(query)

        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows

    except Exception as error:
        print(f"Error: {error}")
        if attempt <= 2:
            return get_search_data(query, data, attempt + 1)
        else:
            return "error"

# Now, let's define the routes for the Flask application.
@app.route('/')
def home():
    return render_template('landing.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        new_user = User(
            username=request.form['username'],
            password=request.form['password'],
            firstname=request.form['firstname'],
            lastname=request.form['lastname'],
            email=request.form['email']
        )
        db.session.add(new_user)
        db.session.commit()
        # Add the user to the session
        session['username'] = request.form['username']
        session['firstname'] = request.form['firstname']
        session['lastname'] = request.form['lastname']
        session['email'] = request.form['email']
        return redirect(url_for('menu'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user:
            if user.password == request.form['password']:
                session['username'] = user.username
                session['firstname'] = user.firstname
                session['lastname'] = user.lastname
                session['email'] = user.email
                return redirect(url_for('menu'))
            else:
                return render_template('login.html', login_failed=True)
        else:
            return render_template('login.html', login_failed=True)
    return render_template('login.html', login_failed=False)

@app.route('/logout')
def logout():
    if session:
      if session['email']: session.pop('email', None)
      if session['username']: session.pop('username', None)
      if session['firstname']: session.pop('firstname', None)
      if session['lastname']: session.pop('lastname', None)
    return redirect(url_for('home'))

@app.route('/menu')
def menu():
    if not session or not session['username'] or not session['firstname'] or not session['lastname'] or not session['email']: return redirect(url_for('home'))
    return render_template('menu.html')

# Again, here is the function to generate the table(s) for the search results.
def generate_table(hshd_num):
    query_string = """
    SELECT transactions.HSHD_NUM, BASKET_NUM, PURCHASE_, products.PRODUCT_NUM, DEPARTMENT, COMMODITY, SPEND,
    UNITS, STORE_R, WEEK_NUM, YEAR, L, AGE_RANGE, MARITAL, INCOME_RANGE, HOMEOWNER, HSHD_COMPOSITION, HH_SIZE, CHILDREN
    FROM ((transactions JOIN households ON transactions.HSHD_NUM = households.HSHD_NUM) 
    JOIN products ON transactions.PRODUCT_NUM = products.PRODUCT_NUM)
    WHERE transactions.HSHD_NUM = ?
    ORDER BY transactions.HSHD_NUM, BASKET_NUM, PURCHASE_, products.PRODUCT_NUM, DEPARTMENT, COMMODITY
    """
    query_res = get_search_data(query_string, [hshd_num])  # Pass `hshd_num` as a list
    if query_res == "error" or not isinstance(query_res, list):
        return "error"
    table_content = ""
    for row in query_res:
        table_content += "<tr>"
        for value in row:
            table_content += f"<td>{value}</td>"
        table_content += "</tr>"
    return table_content

# Route for the search page
@app.route('/search', methods=["GET","POST"])
def search():
    if not session or not session['username'] or not session['firstname'] or not session['lastname'] or not session['email']: return redirect(url_for('home'))
    error_string = "<p style='color: red'>Unable to connect to the database. Please refresh the page and try again.</p>"
    if request.method == "GET":
      table_content = generate_table(10)
      if table_content == "error": return render_template('search.html', table_content=error_string, error=True)
      return render_template('search.html', table_content=table_content, error=False)
    else:
      table_content = generate_table(request.form['hshd_num_input'])
      if table_content == "error": return render_template('search.html', table_content=error_string, error=True)
      if len(table_content) == 0: return render_template('search.html', table_content="<p style='color: red'>No data found.</p>", error=True)
      return render_template('search.html', table_content=table_content, error=False)

# Dashboard route
@app.route('/dashboard')
def dashboard():
    if not session or not session['username'] or not session['firstname'] or not session['lastname'] or not session['email']: return redirect(url_for('home'))
    return render_template('dashboard.html')

# Function to insert data into the database
def insert_data(data, table):
    transactions_query = """
    INSERT INTO transactions (
        BASKET_NUM, HSHD_NUM, PURCHASE_, PRODUCT_NUM, SPEND, UNITS, STORE_R, WEEK_NUM, YEAR
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    households_query = """
    INSERT INTO households (
        HSHD_NUM, L, AGE_RANGE, MARITAL, INCOME_RANGE, HOMEOWNER, HSHD_COMPOSITION, HH_SIZE, CHILDREN
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    products_query = """
    INSERT INTO products (
        PRODUCT_NUM, DEPARTMENT, COMMODITY, BRAND_TY, NATURAL_ORGANIC_FLAG
    ) VALUES (%s, %s, %s, %s, %s)
    """
    queries = [transactions_query, households_query, products_query]
    try:
        for row in data:
            query = queries[int(table)]
            query_res = query_customer_trends(query, row)
            if query_res == "error":
                return "false"
        return "true"
    except Exception as error:
        print(f"Error during data insertion: {error}")
        return "false"

# Route for uploading data
@app.route('/upload', methods=['GET','POST'])
def upload():
    if not session or not session['username'] or not session['firstname'] or not session['lastname'] or not session['email']: return redirect(url_for('home'))
    if request.method == "POST":
        file = request.files['file_upload']
        table = request.form['data_type']
        if file:
            data = file.read().decode('utf-8')
            parsed_data = csv.reader(data.splitlines(), delimiter=',')
            next(parsed_data, None)
            successful = insert_data(list(parsed_data), table)
            return render_template('upload.html', success=successful)
        return render_template('upload.html', success="true")
    return render_template('upload.html', success="none")

# This block of code initializes and runs the Flask application.
# Initially, it attempts to bind the application to port 5000.
# If port 5000 is already in use, it incrementally checks the next available port
# until it finds one that is free. This ensures the application can start without
# conflicting with other processes. Once a free port is found, the Flask app is launched
# in debug mode for development purposes.
if __name__ == "__main__":
    import socket
    port = 5000
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        while True:
            try:
                s.bind(("127.0.0.1", port))
                break
            except OSError:
                port += 1
    app.run(debug=True, port=port)