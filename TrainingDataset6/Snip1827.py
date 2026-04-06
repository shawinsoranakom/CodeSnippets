def get_new_command(command):
    return command.script.replace('ag', 'ag -Q', 1)