async def test_light_component_with_webhook(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    netatmo_auth: AsyncMock,
    camera_type: str,
    camera_id: str,
    camera_entity: str,
) -> None:
    """Test setup with webhook."""
    with selected_platforms([Platform.CAMERA]):
        assert await hass.config_entries.async_setup(config_entry.entry_id)

        await hass.async_block_till_done()

    webhook_id = config_entry.data[CONF_WEBHOOK_ID]
    await hass.async_block_till_done()

    assert hass.states.get(camera_entity).state == "streaming"

    response = {
        "event_type": "light_mode",
        "device_id": camera_id,
        "camera_id": camera_id,
        "event_id": "601dce1560abca1ebad9b723",
        "push_type": f"{camera_type}-light_mode",
        "sub_type": "on",
    }
    await simulate_webhook(hass, webhook_id, response)

    assert hass.states.get(camera_entity).state == "streaming"
    assert hass.states.get(camera_entity).attributes["light_state"] == "on"

    response = {
        "event_type": "light_mode",
        "device_id": camera_id,
        "camera_id": camera_id,
        "event_id": "601dce1560abca1ebad9b723",
        "push_type": f"{camera_type}-light_mode",
        "sub_type": "auto",
    }
    await simulate_webhook(hass, webhook_id, response)

    assert hass.states.get(camera_entity).attributes["light_state"] == "auto"

    response = {
        "event_type": "light_mode",
        "device_id": camera_id,
        "camera_id": camera_id,
        "event_id": "601dce1560abca1ebad9b723",
        "push_type": f"{camera_type}-light_mode",
    }
    await simulate_webhook(hass, webhook_id, response)

    assert hass.states.get(camera_entity).state == "streaming"
    assert hass.states.get(camera_entity).attributes["light_state"] == "auto"