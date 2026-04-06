def match(command):
    return ('set-url' in command.script
            and 'fatal: No such remote' in command.output)