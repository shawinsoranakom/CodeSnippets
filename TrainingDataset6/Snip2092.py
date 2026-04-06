def match(command):
    return ('mkdir' in command.script
            and 'No such file or directory' in command.output)