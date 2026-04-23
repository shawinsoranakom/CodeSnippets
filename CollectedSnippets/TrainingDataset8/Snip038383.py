def help(ctx):
    """Print this help message."""
    # Pretend user typed 'streamlit --help' instead of 'streamlit help'.
    import sys

    # We use _get_command_line_as_string to run some error checks but don't do
    # anything with its return value.
    _get_command_line_as_string()

    assert len(sys.argv) == 2  # This is always true, but let's assert anyway.
    sys.argv[1] = "--help"
    main(prog_name="streamlit")