def test_get_example_for_tools_multiple_tools_with_finish():
    """Test get_example_for_tools with multiple tools including finish."""
    # Uses execute_bash and finish tools
    tools = [
        {
            'type': 'function',
            'function': {
                'name': 'execute_bash',
                'description': 'Execute a bash command in the terminal.',
                'parameters': {  # Params added for completeness, not strictly needed by get_example_for_tools
                    'type': 'object',
                    'properties': {
                        'command': {
                            'type': 'string',
                            'description': 'The bash command to execute.',
                        }
                    },
                    'required': ['command'],
                },
            },
        },
        {
            'type': 'function',
            'function': {
                'name': 'str_replace_editor',
                'description': 'Custom editing tool for viewing, creating and editing files.',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'command': {
                            'type': 'string',
                            'description': 'The commands to run.',
                            'enum': [
                                'view',
                                'create',
                                'str_replace',
                                'insert',
                                'undo_edit',
                            ],
                        },
                        'path': {
                            'type': 'string',
                            'description': 'Absolute path to file or directory.',
                        },
                    },
                    'required': ['command', 'path'],
                },
            },
        },
        {
            'type': 'function',
            'function': {
                'name': 'browser',
                'description': 'Interact with the browser.',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'code': {
                            'type': 'string',
                            'description': 'The Python code that interacts with the browser.',
                        }
                    },
                    'required': ['code'],
                },
            },
        },
        {
            'type': 'function',
            'function': {
                'name': 'finish',
                'description': 'Finish the interaction.',
            },
        },
    ]
    example = get_example_for_tools(tools)
    assert example.startswith(
        "Here's a running example of how to perform a task with the provided tools."
    )
    assert (
        'USER: Create a list of numbers from 1 to 10, and display them in a web page at port 5000.'
        in example
    )

    # Check for execute_bash parts (order matters for get_example_for_tools)
    assert TOOL_EXAMPLES['execute_bash']['check_dir'].strip() in example
    assert TOOL_EXAMPLES['execute_bash']['run_server'].strip() in example
    assert TOOL_EXAMPLES['execute_bash']['kill_server'].strip() in example
    assert TOOL_EXAMPLES['execute_bash']['run_server_again'].strip() in example

    # Check for str_replace_editor parts
    assert TOOL_EXAMPLES['str_replace_editor']['create_file'] in example
    assert TOOL_EXAMPLES['str_replace_editor']['edit_file'] in example

    # Check for browser part
    assert TOOL_EXAMPLES['browser']['view_page'] in example

    # Check for finish part
    assert TOOL_EXAMPLES['finish']['example'] in example