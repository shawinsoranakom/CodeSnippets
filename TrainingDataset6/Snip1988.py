def match(command):
    return ('merge' in command.script
            and 'fatal: refusing to merge unrelated histories' in command.output)