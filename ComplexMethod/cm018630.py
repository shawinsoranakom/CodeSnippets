async def test_state_wireless(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test state of the entity with only Wireless MAC."""
    mocked_device = _create_mocked_device(wired_mac=None, wireless_mac=WIRELESS_MAC)
    entry = MockConfigEntry(domain=songpal.DOMAIN, data=CONF_DATA)
    entry.add_to_hass(hass)

    with _patch_media_player_device(mocked_device):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get(ENTITY_ID)
    assert state.name == FRIENDLY_NAME
    assert state.state == STATE_ON
    attributes = state.as_dict()["attributes"]
    assert attributes["volume_level"] == 0.5
    assert attributes["is_volume_muted"] is False
    assert attributes["source_list"] == ["title1", "title2"]
    assert attributes["source"] == "title2"
    assert attributes["sound_mode_list"] == ["Sound Mode 1", "Sound Mode 2"]
    assert attributes["sound_mode"] == "Sound Mode 2"
    assert attributes["supported_features"] == SUPPORT_SONGPAL

    device = device_registry.async_get_device(
        identifiers={(songpal.DOMAIN, WIRELESS_MAC)}
    )
    assert device.connections == {(dr.CONNECTION_NETWORK_MAC, WIRELESS_MAC)}
    assert device.manufacturer == "Sony Corporation"
    assert device.name == FRIENDLY_NAME
    assert device.sw_version == SW_VERSION
    assert device.model == MODEL

    entity = entity_registry.async_get(ENTITY_ID)
    assert entity.unique_id == WIRELESS_MAC