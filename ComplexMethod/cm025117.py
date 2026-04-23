def test_logarithm(hass: HomeAssistant) -> None:
    """Test logarithm."""
    tests = [
        (4, 2, 2.0),
        (1000, 10, 3.0),
        (math.e, "", 1.0),  # The "" means the default base (e) will be used
    ]

    for value, base, expected in tests:
        assert render(hass, f"{{{{ {value} | log({base}) | round(1) }}}}") == expected

        assert render(hass, f"{{{{ log({value}, {base}) | round(1) }}}}") == expected

    # Test handling of invalid input
    with pytest.raises(TemplateError):
        render(hass, "{{ invalid | log(_) }}")
    with pytest.raises(TemplateError):
        render(hass, "{{ log(invalid, _) }}")
    with pytest.raises(TemplateError):
        render(hass, "{{ 10 | log(invalid) }}")
    with pytest.raises(TemplateError):
        render(hass, "{{ log(10, invalid) }}")

    # Test handling of default return value
    assert render(hass, "{{ 'no_number' | log(10, 1) }}") == 1
    assert render(hass, "{{ 'no_number' | log(10, default=1) }}") == 1
    assert render(hass, "{{ log('no_number', 10, 1) }}") == 1
    assert render(hass, "{{ log('no_number', 10, default=1) }}") == 1
    assert render(hass, "{{ log(0, 10, 1) }}") == 1
    assert render(hass, "{{ log(0, 10, default=1) }}") == 1