def get_new_command(command):
    misspelled_command = regex.findall(command.output)[0]
    return replace_command(command, misspelled_command, _get_operations())