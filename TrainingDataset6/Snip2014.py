def get_new_command(command):
    return re.sub(r"delete", "remove", command.script, 1)