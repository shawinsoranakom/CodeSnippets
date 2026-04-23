def test_get_example_for_tools_multiple_tools():
    """Test that get_example_for_tools generates correct example with multiple tools."""
    tools = [
        {
            'type': 'function',
            'function': {
                'name': 'execute_bash',
                'description': 'Execute a bash command in the terminal.',
                'parameters': {
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
    ]
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
    assert TOOL_EXAMPLES['browser']['view_page'] not in example
    assert TOOL_EXAMPLES['finish']['example'] not in example