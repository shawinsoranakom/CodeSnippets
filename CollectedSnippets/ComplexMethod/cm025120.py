def test_tangent(hass: HomeAssistant) -> None:
    """Test tangent."""
    tests = [
        (0, 0.0),
        (math.pi / 4, 1.0),
        (math.pi, 0.0),
        (math.pi / 6, 0.577),
    ]

    for value, expected in tests:
        assert render(hass, f"{{{{ {value} | tan | round(3) }}}}") == expected
        assert render(hass, f"{{{{ tan({value}) | round(3) }}}}") == expected

    # Test handling of invalid input
    with pytest.raises(TemplateError):
        render(hass, "{{ 'duck' | tan }}")

    # Test handling of default return value
    assert render(hass, "{{ 'no_number' | tan(1) }}") == 1
    assert render(hass, "{{ 'no_number' | tan(default=1) }}") == 1
    assert render(hass, "{{ tan('no_number', 1) }}") == 1
    assert render(hass, "{{ tan('no_number', default=1) }}") == 1