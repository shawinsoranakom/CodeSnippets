def match(command):
    '''
    Match a mistyped command
    '''
    return 'lfs' in command.script and 'Did you mean this?' in command.output