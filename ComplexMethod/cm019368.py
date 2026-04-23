async def test_setup_with_cloud(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """Test if set up with active cloud subscription."""
    await mock_cloud(hass)
    await hass.async_block_till_done()

    with (
        patch("homeassistant.components.cloud.async_is_logged_in", return_value=True),
        patch.object(cloud, "async_is_connected", return_value=True),
        patch.object(cloud, "async_active_subscription", return_value=True),
        patch(
            "homeassistant.components.cloud.async_create_cloudhook",
            return_value="https://hooks.nabu.casa/ABCD",
        ) as fake_create_cloudhook,
        patch(
            "homeassistant.components.cloud.async_delete_cloudhook"
        ) as fake_delete_cloudhook,
        patch(
            "homeassistant.components.netatmo.api.AsyncConfigEntryNetatmoAuth"
        ) as mock_auth,
        patch("homeassistant.components.netatmo.data_handler.PLATFORMS", []),
        patch(
            "homeassistant.components.netatmo.async_get_config_entry_implementation",
        ),
        patch(
            "homeassistant.components.netatmo.webhook_generate_url",
        ),
    ):
        mock_auth.return_value.async_post_api_request.side_effect = partial(
            fake_post_request, hass
        )
        assert await async_setup_component(
            hass, "netatmo", {"netatmo": {"client_id": "123", "client_secret": "abc"}}
        )
        assert cloud.async_active_subscription(hass) is True
        assert cloud.async_is_connected(hass) is True
        fake_create_cloudhook.assert_called_once()

        assert (
            hass.config_entries.async_entries("netatmo")[0].data["cloudhook_url"]
            == "https://hooks.nabu.casa/ABCD"
        )

        await hass.async_block_till_done()
        assert hass.config_entries.async_entries(DOMAIN)

        for entry in hass.config_entries.async_entries("netatmo"):
            await hass.config_entries.async_remove(entry.entry_id)
            fake_delete_cloudhook.assert_called_once()

        await hass.async_block_till_done()
        assert not hass.config_entries.async_entries(DOMAIN)