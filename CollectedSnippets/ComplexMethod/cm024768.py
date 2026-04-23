async def test_setup_discovery_with_manually_configured_network_adapter_one_fails(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test setting up Yeelight by discovery with a manually configured network adapter with one that fails to bind."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: IP_ADDRESS, **CONFIG_ENTRY_DATA}
    )
    config_entry.add_to_hass(hass)

    mocked_bulb = _mocked_bulb()
    with (
        _patch_discovery(),
        patch(f"{MODULE}.AsyncBulb", return_value=mocked_bulb),
        patch(
            "homeassistant.components.zeroconf.network.async_get_adapters",
            return_value=_ADAPTERS_WITH_MANUAL_CONFIG_ONE_FAILING,
        ),
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    assert hass.states.get(ENTITY_BINARY_SENSOR) is not None
    assert hass.states.get(ENTITY_LIGHT) is not None

    # Unload
    assert await hass.config_entries.async_unload(config_entry.entry_id)
    assert hass.states.get(ENTITY_BINARY_SENSOR).state == STATE_UNAVAILABLE
    assert hass.states.get(ENTITY_LIGHT).state == STATE_UNAVAILABLE

    # Remove
    assert await hass.config_entries.async_remove(config_entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_BINARY_SENSOR) is None
    assert hass.states.get(ENTITY_LIGHT) is None

    assert f"Failed to setup listener for ('{FAIL_TO_BIND_IP}', 0)" in caplog.text