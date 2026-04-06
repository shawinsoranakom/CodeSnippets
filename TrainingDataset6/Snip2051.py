def get_new_command(command):
    wrong_task = re.findall(r"Task '(\w+)' is not in your gulpfile",
                            command.output)[0]
    return replace_command(command, wrong_task, get_gulp_tasks())