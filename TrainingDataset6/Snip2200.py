def match(command):
    return ('not authenticated' in command.output
            and 'session has expired' in command.output)