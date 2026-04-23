def test_typeof(hass: HomeAssistant) -> None:
    """Test the typeof debug filter/function."""
    assert render(hass, "{{ True | typeof }}") == "bool"
    assert render(hass, "{{ typeof(True) }}") == "bool"

    assert render(hass, "{{ [1, 2, 3] | typeof }}") == "list"
    assert render(hass, "{{ typeof([1, 2, 3]) }}") == "list"

    assert render(hass, "{{ 1 | typeof }}") == "int"
    assert render(hass, "{{ typeof(1) }}") == "int"

    assert render(hass, "{{ 1.1 | typeof }}") == "float"
    assert render(hass, "{{ typeof(1.1) }}") == "float"

    assert render(hass, "{{ None | typeof }}") == "NoneType"
    assert render(hass, "{{ typeof(None) }}") == "NoneType"

    assert render(hass, "{{ 'Home Assistant' | typeof }}") == "str"
    assert render(hass, "{{ typeof('Home Assistant') }}") == "str"