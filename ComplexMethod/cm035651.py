def test_mcp_action_str_representation():
    """Test the string representation of MCPAction."""
    action = MCPAction(
        name='test_tool',
        arguments={'arg1': 'value1', 'arg2': 42},
        thought='This is a test thought',
    )

    str_repr = str(action)
    assert 'MCPAction' in str_repr
    assert 'THOUGHT: This is a test thought' in str_repr
    assert 'NAME: test_tool' in str_repr
    assert 'ARGUMENTS:' in str_repr
    assert 'arg1' in str_repr
    assert 'value1' in str_repr
    assert '42' in str_repr