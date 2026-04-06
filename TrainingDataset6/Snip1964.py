def match(command):
    return (
        "commit" in command.script_parts
        and "no changes added to commit" in command.output
    )