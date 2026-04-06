def match(command):
    return ('did not match any file(s) known to git' in command.output
            and "Did you forget to 'git add'?" not in command.output)