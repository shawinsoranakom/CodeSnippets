def get_new_command(command):
    misspelled_command = re.findall(r"Unrecognized command '(.*)'",
                                    command.output)[0]
    commands = _get_commands()
    return replace_command(command, misspelled_command, commands)