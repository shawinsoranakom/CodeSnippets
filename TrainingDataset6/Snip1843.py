def match(command):
    return "usage:" in command.output and "maybe you meant:" in command.output