def match(command):
    errors = [no_command, no_website]
    for error in errors:
        if error in command.output:
            return True
    return False