#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import sqlite3
import threading
import traceback
import json
import requests
import os
import logging
from flask import Flask, render_template, abort, g, \
    redirect, session, request, flash, url_for
from werkzeug.contrib.fixers import ProxyFix
from datetime import datetime
from wsgiref import simple_server
from pesto import Response, dispatcher_app
from time import sleep, time, mktime
from collections import namedtuple
from urllib import urlencode
from hashlib import sha256

import config

app = Flask('at')
app.wsgi_app = ProxyFix(app.wsgi_app)
app.secret_key = config.secret_key
app.jinja_env.add_extension('jinja2.ext.i18n')
app.jinja_env.install_null_translations()
app.updater = None

from functools import wraps

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

def req_to_ctx():
    return dict(request.form.iteritems())

@app.template_filter('strfts')
def strfts(ts, format='%d/%m/%Y %H:%M'):
    return datetime.fromtimestamp(ts).strftime(format)

@app.template_filter('wikiurl')
def wikiurl(user):
    return config.wiki_url % { 'login': user }

@app.before_request
def make_connection():
    conn = sqlite3.connect(config.db)
    conn.row_factory = sqlite3.Row
    conn.isolation_level = None # for autocommit mode
    g.db = conn

@app.teardown_request
def close_connection(exception):
    g.db.close()

DeviceInfo = namedtuple('DeviceInfo', ['hwaddr', 'name', 'owner', 'ignored'])

def get_device_info(conn, hwaddr):
    return list(get_device_infos(conn, (hwaddrs,)))[0]

def get_device_infos(conn, hwaddrs):
    stmt = '''select hwaddr, name, ignored, owner from 
        devices where devices.hwaddr in (''' + ','.join(['?'] * len(hwaddrs)) + ')'
    for row in conn.execute(stmt, hwaddrs):
        owner = row['owner'] or ''
        ignored = row['ignored']
        yield DeviceInfo(row['hwaddr'], row['name'], owner, ignored)

class Updater(threading.Thread):
    def __init__(self,  timeout, lease_offset = 0, *a, **kw):
        self.timeout = timeout
        self.lock = threading.Lock()
        self.lease_offset = lease_offset
        self.active = {}
        threading.Thread.__init__(self, *a, **kw)
        self.daemon = True
    def purge_stale(self):
        now = time()
        for addr, (atime, ip, name) in self.active.items():
            if now - atime > self.timeout:
                del self.active[addr]
    def get_active_devices(self):
        self.lock.acquire()
        self.purge_stale()
        r = dict(self.active)
        self.lock.release()
        return r
    def get_device(self, ip):
        for hwaddr, (atime, dip, name) in \
            self.get_active_devices().iteritems():
            if ip == dip:
                return hwaddr, name
        return None, None
    def update(self, hwaddr, atime = None, ip = None, name = None):
        if atime:
            atime -= self.lease_offset
        else:
            atime = time() 
        self.lock.acquire()
        self.active[hwaddr] = (atime, ip, name)
        self.lock.release()
        app.logger.info('updated %s with atime %s and ip %s',
            hwaddr, strfts(atime), ip)

class CapUpdater(Updater):
    def __init__(self, cap_file, *a, **kw):
        self.cap_file = cap_file
        Updater.__init__(self, *a, **kw)
    def run(self):
        while True:
            try:
                with open(self.cap_file, 'r', buffering=0) as f:
                    app.logger.info('Updater ready on cap file %s', self.cap_file)
                    while True:
                        hwaddr = f.readline().strip()
                        if not hwaddr:
                            break
                        self.update(hwaddr)
                app.logger.warning('Cap file %s closed, reopening', self.cap_file)
            except Exception as e:
                app.logger.error('Updater got an exception:\n' + \
                    traceback.format_exc(e))
                sleep(10.0)

class MtimeUpdater(Updater):
    def __init__(self, lease_file, *a, **kw):
        self.lease_file = lease_file
        self.last_modified = 0
        Updater.__init__(self, *a, **kw)
    def file_changed(self, f):
        pass
    def run(self):
        while True:
            try:
                mtime = os.stat(self.lease_file).st_mtime
                if mtime > self.last_modified:
                    app.logger.info('Lease file changed, updating')
                    with open(self.lease_file, 'r') as f:
                        self.file_changed(f)
                self.last_modified = mtime
                sleep(3.0)
            except Exception as e:
                app.logger.error('Updater got an exception:\n' + \
                    traceback.format_exc(e))
                sleep(10.0)

class DnsmasqUpdater(MtimeUpdater):
    def file_changed(self, f):
        for line in f:
            ts, hwaddr, ip, name, client_id = line.split(' ')
            self.update(hwaddr, int(ts), ip, name)

class DhcpdUpdater(MtimeUpdater):
    def file_changed(self, f):
        lease = False
        for line in f:
            line = line.split('#')[0]
            cmd = line.strip().split()
            if not cmd:
                continue
            if lease:
                field = cmd[0]
                if(field == 'starts'):
                    dt = datetime.strptime(' '.join(cmd[2:]), '%Y/%m/%d %H:%M:%S;')
                    atime = mktime(dt.utctimetuple())
                if(field == 'client-hostname'):
                    name = cmd[1][1:-2]
                if(field == 'hardware'):
                    hwaddr = cmd[2][:-1]
                if(field.startswith('}')):
                    lease = False
                    if hwaddr:
                        self.update(hwaddr, atime, ip, name)
            elif cmd[0] == 'lease':
                ip = cmd[1]
                name, hwaddr, atime = [None] * 3
                lease = True
        
@app.route('/')
def main_view():
    return render_template('main.html', **now_at())

@app.route('/api')
def list_all():
    result = now_at()
    def prettify_user((user, atime)):
        return {
            'login': user,
            'timestamp': atime,
            'pretty_time': strfts(atime),
        }
    result['users'] = map(prettify_user, result['users'])
    result['unknown'] = len(result['unknown'])
    return json.dumps(result)

def now_at():
    devices = app.updater.get_active_devices()
    device_infos = list(get_device_infos(g.db, devices.keys()))
    device_infos.sort(key=lambda di: devices.__getitem__)
    users = list(dict((info.owner, devices[info.hwaddr][0]) for info in device_infos 
        if info.owner and not info.ignored).iteritems())
    users.sort(key=lambda (u, a): a, reverse=True)
    unknown = set(devices.keys()) - set(d.hwaddr for d in device_infos)
    return dict(users=users, unknown=unknown)

restrict_to_hs = restrict_ip(prefix=config.claimable_prefix, 
    exclude=config.claimable_exclude)

@app.route('/login', methods=['GET'])
def login_form():
    return render_template('login.html', **req_to_ctx())

@app.route('/login', methods=['POST'])
def login():
    login = request.form.get('login', '').lower()
    pwd = request.form.get('password', '')
    goto = request.values.get('goto') or '/'
    if requests.post('https://auth.hackerspace.pl', verify=False,
            data = { 'login': login, 'password': pwd }).status_code == 200:
        session['login'] = login
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
        if 'login' not in session:
            flash('You must log in to continue', category='error')
            return redirect('/login?' + 
                urlencode({'goto': request.path}))
        return f(*a, **kw)
    return func

@app.route('/claim', methods=['GET'])
@restrict_to_hs
@login_required
def claim_form():
    hwaddr, name = app.updater.get_device(request.remote_addr)
    return render_template('claim.html', hwaddr=hwaddr, name=name)

@app.route('/claim', methods=['POST'])
@restrict_to_hs
@login_required
def claim():
    hwaddr, lease_name = app.updater.get_device(request.remote_addr)
    ctx = None
    if not hwaddr:
        ctx = { 'error': 'Invalid device.' }
    else:
        login = session['login']
        try:
            g.db.execute('insert into devices (hwaddr, name, owner, ignored)\
                values (?, ?, ?, ?)', [hwaddr, request.form['name'], login, False])
            ctx = {}
        except sqlite3.Error as e:
            ctx = { 'error': 'Could not add device! Perhaps someone claimed it?' }
    return render_template('post_claim.html', **ctx)

def get_user_devices(conn, user):
    devs = conn.execute('select hwaddr, name, ignored from devices where\
 owner = ?', [user])
    return (DeviceInfo(row['hwaddr'], row['name'], user, row['ignored']) for
        row in devs)

@app.route('/account', methods=['GET'])
@login_required
def account():
    devices = get_user_devices(g.db, session['login'])
    return render_template('account.html', devices=devices)

def set_ignored(conn, hwaddr, user, value):
    return conn.execute('update devices set ignored = ? where hwaddr = ? and owner = ?',
        [value, hwaddr, user])

def delete_device(conn, hwaddr, user):
    return conn.execute('delete from devices where hwaddr = ? and owner = ?',
        [hwaddr, user])

@app.route('/devices/<id>/<action>/')
@login_required
def device(id, action):
    user = session['login']
    if action == 'hide':
        set_ignored(g.db, id, user, True)
    if action == 'show':
        set_ignored(g.db, id, user, False)
    if action == 'delete':
        delete_device(g.db, id, user)
    return redirect(url_for('account'))

@app.before_first_request
def setup():
    updater = DhcpdUpdater(config.lease_file, config.timeout, config.lease_offset)
    updater.start()
    app.updater = updater


port = 8080
if __name__ == '__main__':
    app.logger.setLevel(logging.DEBUG)
    app.run('0.0.0.0', config.port, debug=config.debug)
