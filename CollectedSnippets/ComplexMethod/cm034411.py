def get_password_defaults(self):
        # Read password aging defaults
        try:
            minweeks = ''
            maxweeks = ''
            warnweeks = ''
            with open("/etc/default/passwd", 'r') as f:
                for line in f:
                    line = line.strip()
                    if (line.startswith('#') or line == ''):
                        continue
                    m = re.match(r'^([^#]*)#(.*)$', line)
                    if m:  # The line contains a hash / comment
                        line = m.group(1)
                    key, value = line.split('=')
                    if key == "MINWEEKS":
                        minweeks = value.rstrip('\n')
                    elif key == "MAXWEEKS":
                        maxweeks = value.rstrip('\n')
                    elif key == "WARNWEEKS":
                        warnweeks = value.rstrip('\n')
        except Exception as err:
            self.module.fail_json(msg="failed to read /etc/default/passwd: %s" % to_native(err))

        return (minweeks, maxweeks, warnweeks)