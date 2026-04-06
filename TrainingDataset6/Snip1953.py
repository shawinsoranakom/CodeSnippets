def match(command):
    return ("fatal: A branch named '" in command.output
            and "' already exists." in command.output)