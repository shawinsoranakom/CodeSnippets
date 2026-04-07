def get_command_line_option(argv, option):
    """
    Return the value of a command line option (which should include leading
    dashes, e.g. '--testrunner') from an argument list. Return None if the
    option wasn't passed or if the argument list couldn't be parsed.
    """
    parser = CommandParser(add_help=False, allow_abbrev=False)
    parser.add_argument(option, dest="value")
    try:
        options, _ = parser.parse_known_args(argv[2:])
    except CommandError:
        return None
    else:
        return options.value