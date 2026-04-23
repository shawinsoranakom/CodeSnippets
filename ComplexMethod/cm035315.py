def get_example_for_tools(tools: list[dict]) -> str:
    """Generate an in-context learning example based on available tools."""
    available_tools = set()
    for tool in tools:
        if tool['type'] == 'function':
            name = tool['function']['name']
            if name == EXECUTE_BASH_TOOL_NAME:
                available_tools.add('execute_bash')
            elif name == STR_REPLACE_EDITOR_TOOL_NAME:
                available_tools.add('str_replace_editor')
            elif name == BROWSER_TOOL_NAME:
                available_tools.add('browser')
            elif name == FINISH_TOOL_NAME:
                available_tools.add('finish')
            elif name == LLM_BASED_EDIT_TOOL_NAME:
                available_tools.add('edit_file')

    if not available_tools:
        return ''

    example = """Here's a running example of how to perform a task with the provided tools.

--------------------- START OF EXAMPLE ---------------------

USER: Create a list of numbers from 1 to 10, and display them in a web page at port 5000.

"""

    # Build example based on available tools
    if 'execute_bash' in available_tools:
        example += TOOL_EXAMPLES['execute_bash']['check_dir']

    if 'str_replace_editor' in available_tools:
        example += TOOL_EXAMPLES['str_replace_editor']['create_file']
    elif 'edit_file' in available_tools:
        example += TOOL_EXAMPLES['edit_file']['create_file']

    if 'execute_bash' in available_tools:
        example += TOOL_EXAMPLES['execute_bash']['run_server']

    if 'browser' in available_tools:
        example += TOOL_EXAMPLES['browser']['view_page']

    if 'execute_bash' in available_tools:
        example += TOOL_EXAMPLES['execute_bash']['kill_server']

    if 'str_replace_editor' in available_tools:
        example += TOOL_EXAMPLES['str_replace_editor']['edit_file']
    elif 'edit_file' in available_tools:
        example += TOOL_EXAMPLES['edit_file']['edit_file']

    if 'execute_bash' in available_tools:
        example += TOOL_EXAMPLES['execute_bash']['run_server_again']

    if 'finish' in available_tools:
        example += TOOL_EXAMPLES['finish']['example']

    example += """
--------------------- END OF EXAMPLE ---------------------

Do NOT assume the environment is the same as in the example above.

--------------------- NEW TASK DESCRIPTION ---------------------
"""
    example = example.lstrip()

    return refine_prompt(example)