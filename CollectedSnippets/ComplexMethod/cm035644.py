def test_get_example_for_tools_all_tools():
    """Test that get_example_for_tools generates correct example with all tools."""
    tools = FNCALL_TOOLS  # FNCALL_TOOLS already includes 'finish'
    example = get_example_for_tools(tools)
    assert example.startswith(
        "Here's a running example of how to perform a task with the provided tools."
    )
    assert (
        'USER: Create a list of numbers from 1 to 10, and display them in a web page at port 5000.'
        in example
    )
    assert TOOL_EXAMPLES['execute_bash']['check_dir'] in example
    assert TOOL_EXAMPLES['execute_bash']['run_server'] in example
    assert TOOL_EXAMPLES['execute_bash']['kill_server'] in example
    assert TOOL_EXAMPLES['str_replace_editor']['create_file'] in example
    assert TOOL_EXAMPLES['str_replace_editor']['edit_file'] in example
    assert TOOL_EXAMPLES['finish']['example'] in example

    # These are not in global FNCALL_TOOLS
    # assert TOOL_EXAMPLES['web_read']['read_docs'] not in example # web_read is removed
    assert TOOL_EXAMPLES['browser']['view_page'] not in example