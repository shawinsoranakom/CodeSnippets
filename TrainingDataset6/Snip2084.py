def match(command):
    return (command.script.startswith(u'man')
            and u'command not found' in command.output.lower())