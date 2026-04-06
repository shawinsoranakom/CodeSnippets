def match(command):
    return ('error: did you mean `' in command.output
            and '` (with two dashes ?)' in command.output)