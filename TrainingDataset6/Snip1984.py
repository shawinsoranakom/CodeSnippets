def match(command):
    return "'master'" in command.output or "'main'" in command.output