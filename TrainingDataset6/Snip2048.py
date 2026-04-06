def get_new_command(command):
    misspelled_task = regex.findall(command.output)[0].split(':')[0]
    tasks = _get_all_tasks()
    fixed = get_closest(misspelled_task, tasks)
    return command.script.replace(' {}'.format(misspelled_task),
                                  ' {}'.format(fixed))