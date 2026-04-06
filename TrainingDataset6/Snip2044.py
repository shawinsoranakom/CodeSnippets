def match(command):
    return 'is a directory' in command.output.lower()