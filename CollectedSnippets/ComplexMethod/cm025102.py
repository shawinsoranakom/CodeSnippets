async def test_async_render_to_info_with_wildcard_matching_state(
    hass: HomeAssistant,
) -> None:
    """Test tracking template with a wildcard."""
    template_complex_str = """

{% for state in states %}
  {% if state.state.startswith('ope') %}
    {{ state.entity_id }}={{ state.state }}
  {% endif %}
{% endfor %}

"""
    hass.states.async_set("cover.office_drapes", "closed")
    hass.states.async_set("cover.office_window", "closed")
    hass.states.async_set("cover.office_skylight", "open")
    hass.states.async_set("cover.x_skylight", "open")
    hass.states.async_set("binary_sensor.door", "on")
    await hass.async_block_till_done()

    info = render_to_info(hass, template_complex_str)

    assert not info.domains
    assert info.entities == set()
    assert info.all_states is True
    assert info.rate_limit == ALL_STATES_RATE_LIMIT

    hass.states.async_set("binary_sensor.door", "off")
    info = render_to_info(hass, template_complex_str)

    assert not info.domains
    assert info.entities == set()
    assert info.all_states is True
    assert info.rate_limit == ALL_STATES_RATE_LIMIT

    template_cover_str = """

{% for state in states.cover %}
  {% if state.state.startswith('ope') %}
    {{ state.entity_id }}={{ state.state }}
  {% endif %}
{% endfor %}

"""
    hass.states.async_set("cover.x_skylight", "closed")
    info = render_to_info(hass, template_cover_str)

    assert info.domains == {"cover"}
    assert info.entities == set()
    assert info.all_states is False
    assert info.rate_limit == DOMAIN_STATES_RATE_LIMIT