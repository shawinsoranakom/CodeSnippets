def _main_run(file, args=None, flag_options=None):
    if args is None:
        args = []

    if flag_options is None:
        flag_options = {}

    command_line = _get_command_line_as_string()

    check_credentials()

    bootstrap.run(file, command_line, args, flag_options)