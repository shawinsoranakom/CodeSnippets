def match(command):
    return ('this module is not yet installed' in command.output.lower() or
            'initialization required' in command.output.lower()
            )