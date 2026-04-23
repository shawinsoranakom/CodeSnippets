def test_remap(hass: HomeAssistant) -> None:
    """Test remap function."""
    # Test function and filter usage in templates, with kitchen sink parameters.
    # We don't check the return value; that's covered by the unit tests below.
    assert render(hass, "{{ remap(5, 0, 6, 0, 740, steps=10) }}")
    assert render(hass, "{{ 50 | remap(0, 100, 0, 10, steps=8) }}")

    # Test basic remapping - scale from 0-10 to 0-100
    assert MathExtension.remap(0, 0, 10, 0, 100) == 0.0
    assert MathExtension.remap(5, 0, 10, 0, 100) == 50.0
    assert MathExtension.remap(10, 0, 10, 0, 100) == 100.0

    # Test with different input and output ranges
    assert MathExtension.remap(50, 0, 100, 0, 10) == 5.0
    assert MathExtension.remap(25, 0, 100, 0, 10) == 2.5

    # Test with negative ranges
    assert MathExtension.remap(0, -10, 10, 0, 100) == 50.0
    assert MathExtension.remap(-10, -10, 10, 0, 100) == 0.0
    assert MathExtension.remap(10, -10, 10, 0, 100) == 100.0

    # Test inverted output range
    assert MathExtension.remap(0, 0, 10, 100, 0) == 100.0
    assert MathExtension.remap(5, 0, 10, 100, 0) == 50.0
    assert MathExtension.remap(10, 0, 10, 100, 0) == 0.0

    # Test values outside input range, and edge modes
    assert MathExtension.remap(15, 0, 10, 0, 100, edges="none") == 150.0
    assert MathExtension.remap(-4, 0, 10, 0, 100, edges="none") == -40.0
    assert MathExtension.remap(15, 0, 10, 0, 80, edges="clamp") == 80.0
    assert MathExtension.remap(-5, 0, 10, -1, 1, edges="clamp") == -1
    assert MathExtension.remap(15, 0, 10, 0, 100, edges="wrap") == 50.0
    assert MathExtension.remap(-5, 0, 10, 0, 100, edges="wrap") == 50.0

    # Test sensor conversion use case: Celsius to Fahrenheit: 0-100°C to 32-212°F
    assert MathExtension.remap(0, 0, 100, 32, 212) == 32.0
    assert MathExtension.remap(100, 0, 100, 32, 212) == 212.0
    assert MathExtension.remap(50, 0, 100, 32, 212) == 122.0

    # Test time conversion use case: 0-60 minutes to 0-360 degrees, with wrap
    assert MathExtension.remap(80, 0, 60, 0, 360, edges="wrap") == 120.0

    # Test percentage to byte conversion (0-100% to 0-255)
    assert MathExtension.remap(0, 0, 100, 0, 255) == 0.0
    assert MathExtension.remap(50, 0, 100, 0, 255) == 127.5
    assert MathExtension.remap(100, 0, 100, 0, 255) == 255.0

    # Test with float precision
    assert MathExtension.remap(2.5, 0, 10, 0, 100) == 25.0
    assert MathExtension.remap(7.5, 0, 10, 0, 100) == 75.0

    # Test error handling
    for case in (
        "{{ remap(5, 10, 10, 0, 100) }}",
        "{{ remap('invalid', 0, 10, 0, 100) }}",
        "{{ remap(5, 'invalid', 10, 0, 100) }}",
        "{{ remap(5, 0, 'invalid', 0, 100) }}",
        "{{ remap(5, 0, 10, 'invalid', 100) }}",
        "{{ remap(5, 0, 10, 0, 'invalid') }}",
    ):
        with pytest.raises(TemplateError):
            render(hass, case)