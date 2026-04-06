def match(command):
    return command.output.startswith("error: invalid option '-") and any(
        " -{}".format(option) in command.script for option in "surqfdvt"
    )