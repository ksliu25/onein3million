import os
import boto
import botocore
import sqlite3
import hashlib
import datetime
from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash

from boto.s3.key import Key

session 

app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'flaskr.db'),
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

def create_s3_key_url(filename):
    return hashlib.md5(filename + datetime.datetime.now().isoformat()).hexdigest()

def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.cli.command('initdb')
def initdb_command():
    init_db()
    print 'Initialized the database.'

#ROUTES

@app.route('/')    
def slideshows():
    db = get_db()
    cur = db.execute('select title, description, soundclip_s3_url from slideshows order by id desc')
    slideshows = cur.fetchall()
    return render_template('show_slideshows.html', slideshows=slideshows)

@app.route('/', methods=['POST'])
def add_slideshow():
    if not session.get('logged_in'):
        abort(401)

    s3 = boto.connect_s3()
    bucket_name = 'onein3million'
    bucket = s3.get_bucket(bucket_name)
    k = Key(bucket)

    data_files = request.files.getlist('file[]')
    for data_file in data_files:
        file_contents = data_file.read()
        #Hash for unique urls even if filenames are same. Defensive coding.
        k.key = create_s3_key_url(data_file.filename)
        print "Uploading some data to " + bucket_name + " with key " + k.key
        k.set_contents_from_string(file_contents)
    new_object_url = "https://s3-us-west-2.amazonaws.com/onein3million/" + k.key
    print "WE'RR HERE!"
    db = get_db()
    db.execute('insert into slideshows (title, blurb, description, soundclip_s3_url) values (?, ?, ?, ?)', [request.form['title'], request.form['blurb'], request.form['description'], new_object_url])
    db.commit()
    flash('New slideshow added!')
    print "ALMOST TO REDIRECT!"
    return redirect(url_for('slideshows'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('slideshows'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('slideshows'))