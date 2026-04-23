def test_mcp_action_with_complex_arguments():
    """Test MCPAction with complex nested arguments."""
    complex_args = {
        'simple_arg': 'value',
        'number_arg': 42,
        'boolean_arg': True,
        'nested_arg': {'inner_key': 'inner_value', 'inner_list': [1, 2, 3]},
        'list_arg': ['a', 'b', 'c'],
    }

    action = MCPAction(name='complex_tool', arguments=complex_args)

    assert action.name == 'complex_tool'
    assert action.arguments == complex_args
    assert action.arguments['nested_arg']['inner_key'] == 'inner_value'
    assert action.arguments['list_arg'] == ['a', 'b', 'c']

    # Check that the message contains the complex arguments
    message = action.message
    assert 'complex_tool' in message
    assert 'nested_arg' in message
    assert 'inner_key' in message
    assert 'inner_value' in message