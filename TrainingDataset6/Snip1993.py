def get_new_command(command):
    line = command.output.split('\n')[-3].strip()
    branch = line.split(' ')[-1]
    set_upstream = line.replace('<remote>', 'origin')\
                       .replace('<branch>', branch)
    return shell.and_(set_upstream, command.script)