async def test_camera_reconnect_webhook(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    camera_type: str,
    camera_id: str,
    camera_entity: str,
    expected_state: str,
) -> None:
    """Test webhook event on camera reconnect."""
    fake_post_hits = 0

    async def fake_post(*args: Any, **kwargs: Any):
        """Fake error during requesting backend data."""
        nonlocal fake_post_hits
        fake_post_hits += 1
        return await fake_post_request(hass, *args, **kwargs)

    with (
        patch(
            "homeassistant.components.netatmo.api.AsyncConfigEntryNetatmoAuth"
        ) as mock_auth,
        patch("homeassistant.components.netatmo.data_handler.PLATFORMS", ["camera"]),
        patch(
            "homeassistant.components.netatmo.async_get_config_entry_implementation",
        ),
        patch(
            "homeassistant.components.netatmo.webhook_generate_url",
        ) as mock_webhook,
    ):
        mock_auth.return_value.async_post_api_request.side_effect = fake_post
        mock_auth.return_value.async_addwebhook.side_effect = AsyncMock()
        mock_auth.return_value.async_dropwebhook.side_effect = AsyncMock()
        mock_webhook.return_value = "https://example.com"
        assert await hass.config_entries.async_setup(config_entry.entry_id)

        await hass.async_block_till_done()

        webhook_id = config_entry.data[CONF_WEBHOOK_ID]

        # Fake webhook activation
        response = {
            "push_type": "webhook_activation",
        }
        await simulate_webhook(hass, webhook_id, response)
        await hass.async_block_till_done()

        assert fake_post_hits == 8

        calls = fake_post_hits

        # Fake camera reconnect
        response = {
            "push_type": f"{camera_type}-connection",
        }
        await simulate_webhook(hass, webhook_id, response)
        await hass.async_block_till_done()

        async_fire_time_changed(
            hass,
            dt_util.utcnow() + timedelta(seconds=60),
        )
        await hass.async_block_till_done()
        assert fake_post_hits >= calls

        # Real camera disconnect
        assert hass.states.get(camera_entity).state == expected_state
        assert hass.states.get(camera_entity).attributes.get("monitoring") is True
        response = {
            "event_type": "disconnection",
            "device_id": camera_id,
            "camera_id": camera_id,
            "event_id": "601dce1560abca1ebad9b723",
            "push_type": f"{camera_type}-disconnection",
        }
        await simulate_webhook(hass, webhook_id, response)

        assert hass.states.get(camera_entity).state == "idle"
        assert hass.states.get(camera_entity).attributes.get("monitoring") is False

        response = {
            "event_type": "connection",
            "device_id": camera_id,
            "camera_id": camera_id,
            "event_id": "646227f1dc0dfa000ec5f350",
            "push_type": f"{camera_type}-connection",
        }
        await simulate_webhook(hass, webhook_id, response)

        assert hass.states.get(camera_entity).state == expected_state
        assert hass.states.get(camera_entity).attributes.get("monitoring") is True