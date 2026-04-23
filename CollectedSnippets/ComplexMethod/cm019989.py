async def test_disable_light_groups(
    hass: HomeAssistant,
    config_entry_setup: MockConfigEntry,
) -> None:
    """Test disallowing light groups work."""
    assert len(hass.states.async_all()) == 1
    assert hass.states.get("light.tunable_white_light")
    assert not hass.states.get("light.light_group")
    assert not hass.states.get("light.empty_group")

    hass.config_entries.async_update_entry(
        config_entry_setup, options={CONF_ALLOW_DECONZ_GROUPS: True}
    )
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 2
    assert hass.states.get("light.light_group")

    hass.config_entries.async_update_entry(
        config_entry_setup, options={CONF_ALLOW_DECONZ_GROUPS: False}
    )
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 1
    assert not hass.states.get("light.light_group")