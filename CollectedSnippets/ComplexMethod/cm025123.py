def test_average(hass: HomeAssistant) -> None:
    """Test the average function."""
    assert render(hass, "{{ average([1, 2, 3]) }}") == 2
    assert render(hass, "{{ average(1, 2, 3) }}") == 2

    # Testing of default values
    assert render(hass, "{{ average([1, 2, 3], -1) }}") == 2
    assert render(hass, "{{ average([], -1) }}") == -1
    assert render(hass, "{{ average([], default=-1) }}") == -1
    assert render(hass, "{{ average([], 5, default=-1) }}") == -1
    assert render(hass, "{{ average(1, 'a', 3, default=-1) }}") == -1

    with pytest.raises(TemplateError):
        render(hass, "{{ average() }}")

    with pytest.raises(TemplateError):
        render(hass, "{{ average([]) }}")