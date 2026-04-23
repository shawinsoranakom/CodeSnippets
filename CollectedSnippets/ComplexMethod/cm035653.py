def test_mcp_observation_with_arguments():
    """Test MCPObservation with arguments."""
    complex_args = {
        'simple_arg': 'value',
        'number_arg': 42,
        'boolean_arg': True,
        'nested_arg': {'inner_key': 'inner_value', 'inner_list': [1, 2, 3]},
        'list_arg': ['a', 'b', 'c'],
    }

    observation = MCPObservation(
        content=json.dumps({'result': 'success', 'data': 'test data'}),
        name='test_tool',
        arguments=complex_args,
    )

    assert observation.content == json.dumps({'result': 'success', 'data': 'test data'})
    assert observation.observation == ObservationType.MCP
    assert observation.name == 'test_tool'
    assert observation.arguments == complex_args
    assert observation.arguments['nested_arg']['inner_key'] == 'inner_value'
    assert observation.arguments['list_arg'] == ['a', 'b', 'c']

    # Test serialization
    from openhands.events.serialization import event_to_dict

    serialized = event_to_dict(observation)

    assert serialized['observation'] == ObservationType.MCP
    assert serialized['content'] == json.dumps(
        {'result': 'success', 'data': 'test data'}
    )
    assert serialized['extras']['name'] == 'test_tool'
    assert serialized['extras']['arguments'] == complex_args
    assert serialized['extras']['arguments']['nested_arg']['inner_key'] == 'inner_value'