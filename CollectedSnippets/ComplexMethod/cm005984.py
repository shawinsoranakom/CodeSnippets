def test_in_recommended_models(mock_component):
    """Test in_recommended_models method."""
    assert mock_component.in_recommended_models("gpt-5.1") is True
    assert mock_component.in_recommended_models("claude-sonnet-4") is True
    assert mock_component.in_recommended_models("gpt-5.1-turbo") is True
    assert mock_component.in_recommended_models("claude-sonnet-4-preview") is True
    assert mock_component.in_recommended_models("gpt-4") is False
    assert mock_component.in_recommended_models("gpt-3.5-turbo") is False
    assert mock_component.in_recommended_models("claude-3") is False