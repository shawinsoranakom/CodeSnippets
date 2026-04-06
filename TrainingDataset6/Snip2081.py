def get_new_command(command):
    command = command.script_parts[:]
    command[0] = 'ls -lah'
    return ' '.join(command)