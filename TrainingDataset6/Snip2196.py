def match(command):
    return ('ambiguous command:' in command.output
            and 'could be:' in command.output)