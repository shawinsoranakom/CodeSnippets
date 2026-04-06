def match(command):
    return ('command not found' in command.output.lower()
            and u' ' in command.script)