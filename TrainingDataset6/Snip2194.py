def match(command):
    return command.script == 'test.py' and 'not found' in command.output