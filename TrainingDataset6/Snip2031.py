def match(command):
    return (command.script.startswith('go run ')
            and not command.script.endswith('.go'))