def get_new_command(command):
    if "'master'" in command.output:
        return command.script.replace("master", "main")
    return command.script.replace("main", "master")