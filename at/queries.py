from collections import namedtuple

DeviceInfo = namedtuple('DeviceInfo', ['hwaddr', 'name', 'owner', 'ignored'])
User = namedtuple('User', ['id', 'login', 'passwd', 'url'])

def get_user_devices(conn, user):
    devs = conn.execute('select hwaddr, name, ignored from devices where\
 owner = ?', [user.id])
    return (DeviceInfo(row['hwaddr'], row['name'], user, row['ignored']) for
        row in devs)

def get_device_info(conn, hwaddr):
    return list(get_device_infos(conn, (hwaddrs,)))[0]

def get_device_infos(conn, hwaddrs):
    stmt = '''select hwaddr, name, ignored, userid, login, url from 
        devices left join users on devices.owner = users.userid
        where devices.hwaddr in (''' + ','.join(['?'] * len(hwaddrs)) + ')'
    for row in conn.execute(stmt, hwaddrs):
        owner = User(row['userid'], row['login'], None, row['url']) \
            if row['login'] else None
        ignored = row['ignored']
        yield DeviceInfo(row['hwaddr'], row['name'], owner, ignored)

def get_user(conn, login, password):
    row = conn.execute('select userid, login, pass, url from users where\
     login = ? and pass = ?', [login, sha256(password).hexdigest()]).fetchone()
    return row and User(row['userid'], row['login'], None, row['url'])
