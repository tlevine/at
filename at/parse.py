def lease_file(fp):
    for line in fp:
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
