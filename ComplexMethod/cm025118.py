def test_sine(hass: HomeAssistant) -> None:
    """Test sine."""
    tests = [
        (0, 0.0),
        (math.pi / 2, 1.0),
        (math.pi, 0.0),
        (math.pi * 1.5, -1.0),
        (math.pi / 10, 0.309),
    ]

    for value, expected in tests:
        assert render(hass, f"{{{{ {value} | sin | round(3) }}}}") == expected
        assert render(hass, f"{{{{ sin({value}) | round(3) }}}}") == expected

    # Test handling of invalid input
    with pytest.raises(TemplateError):
        render(hass, "{{ 'duck' | sin }}")
    with pytest.raises(TemplateError):
        render(hass, "{{ invalid | sin('duck') }}")

    # Test handling of default return value
    assert render(hass, "{{ 'no_number' | sin(1) }}") == 1
    assert render(hass, "{{ 'no_number' | sin(default=1) }}") == 1
    assert render(hass, "{{ sin('no_number', 1) }}") == 1
    assert render(hass, "{{ sin('no_number', default=1) }}") == 1