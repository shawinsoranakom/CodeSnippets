def match(command):
    return ('merge' in command.script
            and ' - not something we can merge' in command.output
            and 'Did you mean this?' in command.output)