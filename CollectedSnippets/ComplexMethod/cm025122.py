def test_arc_functions(hass: HomeAssistant) -> None:
    """Test arc trigonometric functions."""
    # Test arc sine
    assert render(hass, "{{ asin(0.5) | round(3) }}") == round(math.asin(0.5), 3)
    assert render(hass, "{{ 0.5 | asin | round(3) }}") == round(math.asin(0.5), 3)

    # Test arc cosine
    assert render(hass, "{{ acos(0.5) | round(3) }}") == round(math.acos(0.5), 3)
    assert render(hass, "{{ 0.5 | acos | round(3) }}") == round(math.acos(0.5), 3)

    # Test arc tangent
    assert render(hass, "{{ atan(1) | round(3) }}") == round(math.atan(1), 3)
    assert render(hass, "{{ 1 | atan | round(3) }}") == round(math.atan(1), 3)

    # Test atan2
    assert render(hass, "{{ atan2(1, 1) | round(3) }}") == round(math.atan2(1, 1), 3)
    assert render(hass, "{{ atan2([1, 1]) | round(3) }}") == round(math.atan2(1, 1), 3)

    # Test invalid input handling
    with pytest.raises(TemplateError):
        render(hass, "{{ asin(2) }}")  # Outside domain [-1, 1]

    # Test default values
    assert render(hass, "{{ asin(2, 1) }}") == 1
    assert render(hass, "{{ acos(2, 1) }}") == 1
    assert render(hass, "{{ atan('invalid', 1) }}") == 1
    assert render(hass, "{{ atan2('invalid', 1, 1) }}") == 1