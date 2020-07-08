import datetime
import json

import requests
from flask import render_template, redirect, request

from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re

from app import app

CONNECTED_NODE_CHAIN_ADDRESS = "http://127.0.0.1:8000/chain"
CONNECTED_NODE_NEW_TX_ADDRESS = "http://127.0.0.1:8000/transactions/new"

posts = []

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'your secret key'

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Breezyteapot009'
app.config['MYSQL_DB'] = 'pythonlogin'

# Intialize MySQL
mysql = MySQL(app)


# http://localhost:5000/pythonlogin/ - this will be the login page, we need to use both GET and POST requests
@app.route('/', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            # Redirect to home page
            return redirect(url_for('index'))

        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    # Show the login form with message (if any)
    return render_template('login.html', msg=msg)


# http://localhost:5000/python/logout - this will be the logout page
@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    # Redirect to login page
    return redirect(url_for('login'))


# http://localhost:5000/pythinlogin/register - this will be the registration page, we need to use both GET and POST requests
@app.route('/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s)', (username, password, email,))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)


# http://localhost:5000/pythinlogin/home - this will be the home page, only accessible for loggedin users

@app.route('/home')
def index():
    return render_template('index.html',
                           title='Prototype ',
                           posts=posts)


def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('index.html', author=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


@app.route('/submit', methods=['POST'])
def submit_textarea():
    post_content = request.form["body"]
    author = session['username']

    print("Valid args receiveds")

    post_object = {
        'author': author,
        'body': post_content,
        'time': datetime.datetime.now().strftime('%H:%M')
    }

    res = requests.post(CONNECTED_NODE_NEW_TX_ADDRESS,
                        json=post_object,
                        headers={'Content-type': 'application/json'})

    if res.status_code == 201:
        print(res.text)

    return redirect('/fetch')


# FIXME: Develop a server_node endpoint for this.
@app.route('/fetch', methods=['POST', 'GET'])
def fetch_posts():
    resp = requests.get(CONNECTED_NODE_CHAIN_ADDRESS)
    if resp.status_code == 200:
        content = []
        chain = json.loads(resp.content)
        for block in chain["chain"]:
            for tx in block["transactions"]:
                # Adding just for visiblity
                tx["index"] = block["index"]
                tx["hash"] = block["previous_hash"]
                content.append(tx)

        global posts
        posts = sorted(content, key=lambda k: k['server_timestamp'], reverse=True)

    else:
        print("Some Error ocurred while fetching the chain")

    return redirect('/home')


'''
Sample chain response
{
  "chain": [
    {
      "index": 1, 
      "previous_hash": "1", 
      "proof": 100, 
      "timestamp": 1512904176.946647, 
      "transactions": []
    }, 
    {
      "index": 2, 
      "previous_hash": "a2728924c133546671e71cb9d9951f6e68b488deae483c2527f281b2a9e35491", 
      "proof": 35293, 
      "timestamp": 1512904218.593914, 
      "transactions": [
        {
          "author": "fsjklfjds", 
          "body": "Hello basdf", 
          "time": "16:40:18"
        }
      ]
    }
  ], 
  "length": 2
}
'''
