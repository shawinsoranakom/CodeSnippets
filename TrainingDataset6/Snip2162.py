def match(command):
    return ('rm' in command.script
            and 'is a directory' in command.output.lower())