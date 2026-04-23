def test_remap_with_steps(hass: HomeAssistant) -> None:
    """Test remap function with steps parameter."""
    # Test basic stepping - quantize to 10 steps
    assert MathExtension.remap(0.2, 0, 10, 0, 100, steps=10) == 0.0
    assert MathExtension.remap(5.3, 0, 10, 0, 100, steps=10) == 50.0
    assert MathExtension.remap(10, 0, 10, 0, 100, steps=10) == 100.0

    # Test stepping with intermediate values - should snap to nearest step
    # With 10 steps, normalized values are rounded: 0.0, 0.1, 0.2, ..., 1.0
    assert MathExtension.remap(2.4, 0, 10, 0, 100, steps=10) == 20.0
    assert MathExtension.remap(2.5, 0, 10, 0, 100, steps=10) == 20.0
    assert MathExtension.remap(2.6, 0, 10, 0, 100, steps=10) == 30.0

    # Test with 4 steps (0%, 25%, 50%, 75%, 100%)
    assert MathExtension.remap(0, 0, 10, 0, 100, steps=4) == 0.0
    assert MathExtension.remap(2.5, 0, 10, 0, 100, steps=4) == 25.0
    assert MathExtension.remap(5, 0, 10, 0, 100, steps=4) == 50.0
    assert MathExtension.remap(7.5, 0, 10, 0, 100, steps=4) == 75.0
    assert MathExtension.remap(10, 0, 10, 0, 100, steps=4) == 100.0

    # Test with 2 steps (0%, 50%, 100%)
    assert MathExtension.remap(2, 0, 10, 0, 100, steps=2) == 0.0
    assert MathExtension.remap(6, 0, 10, 0, 100, steps=2) == 50.0
    assert MathExtension.remap(8, 0, 10, 0, 100, steps=2) == 100.0

    # Test with 1 step (0%, 100%)
    assert MathExtension.remap(0, 0, 10, 0, 100, steps=1) == 0.0
    assert MathExtension.remap(5, 0, 10, 0, 100, steps=1) == 0.0
    assert MathExtension.remap(6, 0, 10, 0, 100, steps=1) == 100.0
    assert MathExtension.remap(10, 0, 10, 0, 100, steps=1) == 100.0

    # Test with inverted output range and steps
    assert MathExtension.remap(4.8, 0, 10, 100, 0, steps=4) == 50.0

    # Test with 0 or negative steps (should be ignored/no quantization)
    assert MathExtension.remap(5, 0, 10, 0, 100, steps=0) == 50.0
    assert MathExtension.remap(2.7, 0, 10, 0, 100, steps=0) == 27.0
    assert MathExtension.remap(5, 0, 10, 0, 100, steps=-1) == 50.0