def _command_to_string(command):
    if isinstance(command, list):
        return " ".join(command)
    else:
        return command