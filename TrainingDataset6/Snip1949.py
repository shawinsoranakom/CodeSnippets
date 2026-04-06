def match(command):
    return ('branch -d' in command.script
            and 'If you are sure you want to delete it' in command.output)