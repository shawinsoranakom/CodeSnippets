def match(command):
    return ('stash' in command.script
            and 'pop' in command.script
            and 'Your local changes to the following files would be overwritten by merge' in command.output)