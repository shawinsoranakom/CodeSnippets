async def test_setup_component_with_webhook(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    netatmo_auth: AsyncMock,
    camera_type: str,
    camera_id: str,
    camera_entity: str,
    expected_state: str,
) -> None:
    """Test setup with webhook."""
    with selected_platforms([Platform.CAMERA]):
        assert await hass.config_entries.async_setup(config_entry.entry_id)

        await hass.async_block_till_done()

    webhook_id = config_entry.data[CONF_WEBHOOK_ID]
    await hass.async_block_till_done()

    # Test on/off camera events
    assert hass.states.get(camera_entity).state == expected_state
    assert hass.states.get(camera_entity).attributes.get("monitoring") is True
    response = {
        "event_type": "off",
        "device_id": camera_id,
        "camera_id": camera_id,
        "event_id": "601dce1560abca1ebad9b723",
        "push_type": f"{camera_type}-off",
    }
    await simulate_webhook(hass, webhook_id, response)

    assert hass.states.get(camera_entity).state == "idle"
    assert hass.states.get(camera_entity).attributes.get("monitoring") is False

    response = {
        "event_type": "on",
        "device_id": camera_id,
        "camera_id": camera_id,
        "event_id": "646227f1dc0dfa000ec5f350",
        "push_type": f"{camera_type}-on",
    }
    await simulate_webhook(hass, webhook_id, response)

    assert hass.states.get(camera_entity).state == expected_state
    assert hass.states.get(camera_entity).attributes.get("monitoring") is True

    # Test turn_on/turn_off services
    with patch("pyatmo.home.Home.async_set_state") as mock_set_state:
        await hass.services.async_call(
            "camera", "turn_off", service_data={"entity_id": camera_entity}
        )
        await hass.async_block_till_done()
        mock_set_state.assert_called_once_with(
            {
                "modules": [
                    {
                        "id": camera_id,
                        "monitoring": "off",
                    }
                ]
            }
        )

    with patch("pyatmo.home.Home.async_set_state") as mock_set_state:
        await hass.services.async_call(
            "camera", "turn_on", service_data={"entity_id": camera_entity}
        )
        await hass.async_block_till_done()
        mock_set_state.assert_called_once_with(
            {
                "modules": [
                    {
                        "id": camera_id,
                        "monitoring": "on",
                    }
                ]
            }
        )