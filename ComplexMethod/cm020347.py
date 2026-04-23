async def test_setup_with_defaults_v6(hass: HomeAssistant) -> None:
    """Tests component setup with default config."""
    mocked_hole = _create_mocked_hole(
        api_version=6, has_data=True, incorrect_app_password=False
    )
    entry = MockConfigEntry(
        domain=pi_hole.DOMAIN, data={**CONFIG_DATA_DEFAULTS, CONF_STATISTICS_ONLY: True}
    )
    entry.add_to_hass(hass)
    with _patch_init_hole(mocked_hole):
        assert await hass.config_entries.async_setup(entry.entry_id)

    state = hass.states.get("sensor.pi_hole_ads_blocked")
    assert state is not None
    assert state.name == "Pi-Hole Ads blocked"
    assert state.state == "0"

    state = hass.states.get("sensor.pi_hole_ads_percentage_blocked")
    assert state.name == "Pi-Hole Ads percentage blocked"
    assert state.state == "0"

    state = hass.states.get("sensor.pi_hole_dns_queries_cached")
    assert state.name == "Pi-Hole DNS queries cached"
    assert state.state == "0"

    state = hass.states.get("sensor.pi_hole_dns_queries_forwarded")
    assert state.name == "Pi-Hole DNS queries forwarded"
    assert state.state == "0"

    state = hass.states.get("sensor.pi_hole_dns_queries")
    assert state.name == "Pi-Hole DNS queries"
    assert state.state == "0"

    state = hass.states.get("sensor.pi_hole_dns_unique_clients")
    assert state.name == "Pi-Hole DNS unique clients"
    assert state.state == "0"

    state = hass.states.get("sensor.pi_hole_dns_unique_domains")
    assert state.name == "Pi-Hole DNS unique domains"
    assert state.state == "0"

    state = hass.states.get("sensor.pi_hole_domains_blocked")
    assert state.name == "Pi-Hole Domains blocked"
    assert state.state == "0"

    state = hass.states.get("sensor.pi_hole_seen_clients")
    assert state.name == "Pi-Hole Seen clients"
    assert state.state == "0"

    state = hass.states.get("binary_sensor.pi_hole_status")
    assert state.name == "Pi-Hole Status"
    assert state.state == "off"