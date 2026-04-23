def test_prog_name():
    """Assert that the program name is set to `streamlit test`.

    This is used by our cli-smoke-tests to verify that the program name is set
    to `streamlit ...` whether the streamlit binary is invoked directly or via
    `python -m streamlit ...`.
    """
    # We use _get_command_line_as_string to run some error checks but don't do
    # anything with its return value.
    _get_command_line_as_string()

    parent = click.get_current_context().parent

    assert parent is not None
    assert parent.command_path == "streamlit test"