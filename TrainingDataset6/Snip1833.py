def get_new_command(command):
    return re.sub(r'^apt-get', 'apt-cache', command.script)