def get_new_command(command):
    wrong_task = regex.findall(command.output)[0][0]
    all_tasks = _get_all_tasks(command.script_parts[0])
    return replace_command(command, wrong_task, all_tasks)