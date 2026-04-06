def match(command):
    files = [arg for arg in command.script_parts[2:]
             if not arg.startswith('-')]
    return ('diff' in command.script
            and '--no-index' not in command.script
            and len(files) == 2)