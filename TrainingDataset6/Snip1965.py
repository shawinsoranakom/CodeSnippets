def get_new_command(command):
    for opt in ("-a", "-p"):
        yield replace_argument(command.script, "commit", "commit {}".format(opt))