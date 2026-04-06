def match(command):
    return ('-s' in command.script_parts
            and command.script_parts[-1] != '-s')