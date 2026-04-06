def match(command):
    return (('did you mean this?' in command.output.lower()
             or 'did you mean one of these?' in command.output.lower())) or (
        "install" in command.script_parts and "composer require" in command.output.lower()
    )