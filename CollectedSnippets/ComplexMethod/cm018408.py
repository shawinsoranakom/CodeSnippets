async def test_setup_with_cloud(
    hass: HomeAssistant,
    webhook_config_entry: MockConfigEntry,
    withings: AsyncMock,
    freezer: FrozenDateTimeFactory,
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
            "homeassistant.components.withings.async_get_config_entry_implementation",
        ),
        patch(
            "homeassistant.components.cloud.async_delete_cloudhook"
        ) as fake_delete_cloudhook,
        patch("homeassistant.components.withings.webhook_generate_url"),
    ):
        await setup_integration(hass, webhook_config_entry)
        await prepare_webhook_setup(hass, freezer)

        assert cloud.async_active_subscription(hass) is True
        assert cloud.async_is_connected(hass) is True
        fake_create_cloudhook.assert_called_once()
        fake_delete_cloudhook.assert_called_once()

        assert (
            hass.config_entries.async_entries("withings")[0].data["cloudhook_url"]
            == "https://hooks.nabu.casa/ABCD"
        )

        await hass.async_block_till_done()
        assert hass.config_entries.async_entries(DOMAIN)

        for config_entry in hass.config_entries.async_entries("withings"):
            await hass.config_entries.async_remove(config_entry.entry_id)
            assert fake_delete_cloudhook.call_count == 2

        await hass.async_block_till_done()
        assert not hass.config_entries.async_entries(DOMAIN)