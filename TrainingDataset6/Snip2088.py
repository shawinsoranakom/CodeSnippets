def get_new_command(command):
    script = command.script_parts[:]
    possibilities = extract_possibilities(command)
    script[1] = get_closest(script[1], possibilities)
    return ' '.join(script)