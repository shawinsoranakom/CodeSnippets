def match(command):
    output = command.output.lower()
    return 'omitting directory' in output or 'is a directory' in output