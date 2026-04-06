def match(command):
    return ('pull' in command.script
            and ('You have unstaged changes' in command.output
                 or 'contains uncommitted changes' in command.output))