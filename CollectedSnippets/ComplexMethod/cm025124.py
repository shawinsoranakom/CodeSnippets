def test_clamp(hass: HomeAssistant) -> None:
    """Test clamp function."""
    # Test function and filter usage in templates.
    assert render(hass, "{{ clamp(15, 0, 10) }}") == 10.0
    assert render(hass, "{{ -5 | clamp(0, 10) }}") == 0.0

    # Test basic clamping behavior
    assert MathExtension.clamp(5, 0, 10) == 5.0
    assert MathExtension.clamp(-5, 0, 10) == 0.0
    assert MathExtension.clamp(15, 0, 10) == 10.0
    assert MathExtension.clamp(0, 0, 10) == 0.0
    assert MathExtension.clamp(10, 0, 10) == 10.0

    # Test with float values
    assert MathExtension.clamp(5.5, 0, 10) == 5.5
    assert MathExtension.clamp(5.5, 0.5, 10.5) == 5.5
    assert MathExtension.clamp(0.25, 0.5, 10.5) == 0.5
    assert MathExtension.clamp(11.0, 0.5, 10.5) == 10.5

    # Test with negative ranges
    assert MathExtension.clamp(-5, -10, -1) == -5.0
    assert MathExtension.clamp(-15, -10, -1) == -10.0
    assert MathExtension.clamp(0, -10, -1) == -1.0

    # Test with non-range
    assert MathExtension.clamp(5, 10, 10) == 10.0

    # Test error handling - invalid input types
    for case in (
        "{{ clamp('invalid', 0, 10) }}",
        "{{ clamp(5, 'invalid', 10) }}",
        "{{ clamp(5, 0, 'invalid') }}",
    ):
        with pytest.raises(TemplateError):
            render(hass, case)