def get_new_command(command):
    return re.sub(r'^cp', 'cp -a', command.script)