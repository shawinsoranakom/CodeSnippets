def get_new_command(command):
    return re.sub('\\bmkdir (.*)', 'mkdir -p \\1', command.script)