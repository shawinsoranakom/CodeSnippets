def test_wrap(hass: HomeAssistant) -> None:
    """Test wrap function."""
    # Test function and filter usage in templates.
    assert render(hass, "{{ wrap(15, 0, 10) }}") == 5.0
    assert render(hass, "{{ -5 | wrap(0, 10) }}") == 5.0

    # Test basic wrapping behavior
    assert MathExtension.wrap(5, 0, 10) == 5.0
    assert MathExtension.wrap(10, 0, 10) == 0.0  # max wraps to min
    assert MathExtension.wrap(15, 0, 10) == 5.0
    assert MathExtension.wrap(25, 0, 10) == 5.0
    assert MathExtension.wrap(-5, 0, 10) == 5.0
    assert MathExtension.wrap(-10, 0, 10) == 0.0

    # Test angle wrapping (common use case)
    assert MathExtension.wrap(370, 0, 360) == 10.0
    assert MathExtension.wrap(-10, 0, 360) == 350.0
    assert MathExtension.wrap(720, 0, 360) == 0.0
    assert MathExtension.wrap(361, 0, 360) == 1.0

    # Test with float values
    assert MathExtension.wrap(10.5, 0, 10) == 0.5
    assert MathExtension.wrap(370.5, 0, 360) == 10.5

    # Test with negative ranges
    assert MathExtension.wrap(-15, -10, 0) == -5.0
    assert MathExtension.wrap(5, -10, 0) == -5.0

    # Test with arbitrary ranges
    assert MathExtension.wrap(25, 10, 20) == 15.0
    assert MathExtension.wrap(5, 10, 20) == 15.0

    # Test with non-range
    assert MathExtension.wrap(5, 10, 10) == 10.0

    # Test error handling - invalid input types
    for case in (
        "{{ wrap('invalid', 0, 10) }}",
        "{{ wrap(5, 'invalid', 10) }}",
        "{{ wrap(5, 0, 'invalid') }}",
    ):
        with pytest.raises(TemplateError):
            render(hass, case)