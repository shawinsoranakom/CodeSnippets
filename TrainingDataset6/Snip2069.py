def match(command):
    return (command.script.startswith('lein')
            and "is not a task. See 'lein help'" in command.output
            and 'Did you mean this?' in command.output)