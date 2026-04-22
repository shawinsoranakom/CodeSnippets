def main_version(ctx):
    """Print Streamlit's version number."""
    # Pretend user typed 'streamlit --version' instead of 'streamlit version'
    import sys

    # We use _get_command_line_as_string to run some error checks but don't do
    # anything with its return value.
    _get_command_line_as_string()

    assert len(sys.argv) == 2  # This is always true, but let's assert anyway.
    sys.argv[1] = "--version"
    main()