def test_cosine(hass: HomeAssistant) -> None:
    """Test cosine."""
    tests = [
        (0, 1.0),
        (math.pi / 2, 0.0),
        (math.pi, -1.0),
        (math.pi * 1.5, 0.0),
        (math.pi / 3, 0.5),
    ]

    for value, expected in tests:
        assert render(hass, f"{{{{ {value} | cos | round(3) }}}}") == expected
        assert render(hass, f"{{{{ cos({value}) | round(3) }}}}") == expected

    # Test handling of invalid input
    with pytest.raises(TemplateError):
        render(hass, "{{ 'duck' | cos }}")

    # Test handling of default return value
    assert render(hass, "{{ 'no_number' | cos(1) }}") == 1
    assert render(hass, "{{ 'no_number' | cos(default=1) }}") == 1
    assert render(hass, "{{ cos('no_number', 1) }}") == 1
    assert render(hass, "{{ cos('no_number', default=1) }}") == 1