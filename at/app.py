from urllib import urlencode
from hashlib import sha256
import logging
import sqlite3
from datetime import datetime
from functools import wraps, partial
import queries

from werkzeug.contrib.fixers import ProxyFix
from flask import Flask, render_template, abort, g, \
    redirect, session, request, flash, url_for

import util
from updater import DhcpdUpdater
from config import parser
config = parser.parse_args()

# Logging
sink = logging.StreamHandler() # stderr
if config.debug:
    sink.setLevel(logging.DEBUG)
else:
    sink.setLevel(logging.ERROR)

# Configure the app
app = Flask('at')
app.logger.addHandler(sink)
app.wsgi_app = ProxyFix(app.wsgi_app)
app.secret_key = config.secret_key
app.jinja_env.add_extension('jinja2.ext.i18n')
app.jinja_env.install_null_translations()

def restrict_ip(prefix='', exclude=[]):
    def decorator(f):
        @wraps(f)
        def func(*a, **kw):
            r_addr = request.remote_addr
            if not r_addr.startswith(prefix) or r_addr in exclude:
                abort(403)
            return f(*a, **kw)
        return func
    return decorator

restrict_to_hs = restrict_ip(prefix=config.claimable_prefix, 
    exclude=config.claimable_exclude)

def req_to_ctx():
    return dict(request.form.iteritems())

@app.before_request
def make_connection():
    conn = sqlite3.connect(config.db)
    conn.row_factory = sqlite3.Row
    conn.isolation_level = None # for autocommit mode
    g.db = conn

@app.teardown_request
def close_connection(exception):
    g.db.close()
        
@app.route('/')
def main_view():
    return render_template('main.html', **now_at(g.active_devices, g.db))

@app.route('/api')
def list_all():
    result = now_at(g.active_devices, g.db)
    def prettify_user((user, atime)):
        return {
            'login': user.login,
            'timestamp': atime,
            'pretty_time': util.strfts(atime),
            'url': user.url,
        }
    result['users'] = map(prettify_user, result['users'])
    result['unknown'] = len(result['unknown'])
    return json.dumps(result)

@app.route('/register', methods=['GET'])
@restrict_to_hs
def register_form():
    return render_template('register.html', **req_to_ctx())

@app.route('/register', methods=['POST'])
@restrict_to_hs
def register():
    login = request.form['login'].lower()
    url = request.form['url']
    if 'wiki' in request.form:
        url = config.wiki_url % { 'login': login }
    try:
        g.db.execute('insert into users (login, url, pass) values (?, ?, ?)',
            [login, url, sha256(request.form['password']).hexdigest()])
        return redirect('/')
    except sqlite3.Error as e:
        flash('Cannot add user - username taken?', category='error')
        return register_form()

@app.route('/login', methods=['GET'])
def login_form():
    return render_template('login.html', **req_to_ctx())

@app.route('/login', methods=['POST'])
def login():
    login = request.form.get('login', '').lower()
    pwd = request.form.get('password', '')
    goto = request.values.get('goto') or '/'
    user = get_user(g.db, login, pwd)
    if user:
        session['userid'] = user.id
        session['login'] = user.login
        session['user'] = user
        return redirect(goto)
    else:
        flash('Username or password invalid', category='error')
        return login_form()

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

def login_required(f):
    @wraps(f)
    def func(*a, **kw):
        if 'userid' not in session:
            flash('You must log in to continue', category='error')
            return redirect('/login?' + 
                urlencode({'goto': request.path}))
        return f(*a, **kw)
    return func

@app.route('/claim', methods=['GET'])
@restrict_to_hs
@login_required
def claim_form():
    hwaddr, name = updater.get_device(g.active_devices, request.remote_addr)
    return render_template('claim.html', hwaddr=hwaddr, name=name)

@app.route('/claim', methods=['POST'])
@restrict_to_hs
@login_required
def claim():
    hwaddr, lease_name = updater.get_device(g.active_devices, request.remote_addr)
    ctx = None
    if not hwaddr:
        ctx = { 'error': 'Invalid device.' }
    else:
        userid = session['userid']
        try:
            g.db.execute('insert into devices (hwaddr, name, owner, ignored)\
                values (?, ?, ?, ?)', [hwaddr, request.form['name'], userid, False])
            ctx = {}
        except sqlite3.Error as e:
            ctx = { 'error': 'Could not add device! Perhaps someone claimed it?' }
    return render_template('post_claim.html', **ctx)

def set_password(conn, user, password):
    return conn.execute('update users set pass = ? where userid = ?',
        [sha256(password).hexdigest(), user.id])

@app.route('/account', methods=['GET','POST'])
@login_required
def account():
    if request.method == 'POST':
        old = request.form['old']
        if get_user(g.db, session['login'], old) and \
            set_password(g.db, session['user'], request.form['new']):
                flash('Password changed', category='message')
        else:
            flash('Could not change password!', category='error')
    devices = get_user_devices(g.db, session['user'])
    return render_template('account.html', devices=devices)

def set_ignored(conn, hwaddr, user, value):
    return conn.execute('update devices set ignored = ? where hwaddr = ? and owner = ?',
        [value, hwaddr, user.id])

def delete_device(conn, hwaddr, user):
    return conn.execute('delete from devices where hwaddr = ? and owner = ?',
        [hwaddr, user.id])

@app.route('/devices/<id>/<action>/')
@login_required
def device(id, action):
    user = session['user']
    if action == 'hide':
        set_ignored(g.db, id, user, True)
    if action == 'show':
        set_ignored(g.db, id, user, False)
    if action == 'delete':
        delete_device(g.db, id, user)
    return redirect(url_for('account'))

def main():
    updater = DhcpdUpdater(config.lease_file, config.timeout, config.lease_offset)
    updater.start()
    app.run('0.0.0.0', config.port, debug=config.debug)
    g.updater = updater
