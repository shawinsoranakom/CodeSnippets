def get_new_command(command):
    return re.sub(r'^ln ', 'ln -s ', command.script)