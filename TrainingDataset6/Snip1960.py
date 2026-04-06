def match(command):
    return (' git clone ' in command.script
            and 'fatal: Too many arguments.' in command.output)