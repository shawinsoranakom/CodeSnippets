def get_new_command(command):
    misspelled_task = regex.findall(command.output)[0]
    if misspelled_task in npm_commands:
        yarn_command = npm_commands[misspelled_task]
        return replace_argument(command.script, misspelled_task, yarn_command)
    else:
        tasks = _get_all_tasks()
        return replace_command(command, misspelled_task, tasks)