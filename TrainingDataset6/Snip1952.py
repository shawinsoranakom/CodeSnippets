def get_new_command(command):
    return shell.and_("git checkout master", "{}").format(
        replace_argument(command.script, "-d", "-D")
    )