def get_new_command(command):
    broken_cmd = re.findall(r"'([^']*)' is not a task",
                            command.output)[0]
    new_cmds = get_all_matched_commands(command.output, 'Did you mean this?')
    return replace_command(command, broken_cmd, new_cmds)