def get_new_command(command):
    cmd = command.script_parts[:]
    cmd[-1], cmd[-2] = cmd[-2], cmd[-1]
    return ' '.join(cmd)