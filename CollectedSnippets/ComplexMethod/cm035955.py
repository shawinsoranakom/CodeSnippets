def test_featurizer_tool_description(featurizer):
    """Test tool_description property."""
    tool_desc = featurizer.tool_description
    assert tool_desc['type'] == 'function'
    assert tool_desc['function']['name'] == 'call_featurizer'
    assert 'description' in tool_desc['function']

    # Check that all features are included in the properties
    properties = tool_desc['function']['parameters']['properties']
    for feature in featurizer.features:
        assert feature.identifier in properties
        assert properties[feature.identifier]['type'] == 'boolean'
        assert properties[feature.identifier]['description'] == feature.description