def test_square_root(hass: HomeAssistant) -> None:
    """Test square root."""
    tests = [
        (0, 0.0),
        (1, 1.0),
        (4, 2.0),
        (9, 3.0),
        (16, 4.0),
        (0.25, 0.5),
    ]

    for value, expected in tests:
        assert render(hass, f"{{{{ {value} | sqrt }}}}") == expected
        assert render(hass, f"{{{{ sqrt({value}) }}}}") == expected

    # Test handling of invalid input
    with pytest.raises(TemplateError):
        render(hass, "{{ 'duck' | sqrt }}")
    with pytest.raises(TemplateError):
        render(hass, "{{ -1 | sqrt }}")

    # Test handling of default return value
    assert render(hass, "{{ 'no_number' | sqrt(1) }}") == 1
    assert render(hass, "{{ 'no_number' | sqrt(default=1) }}") == 1
    assert render(hass, "{{ sqrt('no_number', 1) }}") == 1
    assert render(hass, "{{ sqrt('no_number', default=1) }}") == 1
    assert render(hass, "{{ sqrt(-1, 1) }}") == 1
    assert render(hass, "{{ sqrt(-1, default=1) }}") == 1