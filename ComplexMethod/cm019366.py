async def test_setup_component(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """Test setup and teardown of the netatmo component."""
    with (
        patch(
            "homeassistant.components.netatmo.api.AsyncConfigEntryNetatmoAuth",
        ) as mock_auth,
        patch(
            "homeassistant.components.netatmo.async_get_config_entry_implementation",
        ) as mock_impl,
        patch("homeassistant.components.netatmo.webhook_generate_url") as mock_webhook,
    ):
        mock_auth.return_value.async_post_api_request.side_effect = partial(
            fake_post_request, hass
        )
        mock_auth.return_value.async_addwebhook.side_effect = AsyncMock()
        mock_auth.return_value.async_dropwebhook.side_effect = AsyncMock()
        assert await async_setup_component(hass, "netatmo", {})

    await hass.async_block_till_done()

    mock_auth.assert_called_once()
    mock_impl.assert_called_once()
    mock_webhook.assert_called_once()

    assert config_entry.state is ConfigEntryState.LOADED
    assert hass.config_entries.async_entries(DOMAIN)
    assert len(hass.states.async_all()) > 0

    for entry in hass.config_entries.async_entries("netatmo"):
        await hass.config_entries.async_remove(entry.entry_id)

    await hass.async_block_till_done()
    assert len(hass.states.async_all()) == 0
    assert not hass.config_entries.async_entries(DOMAIN)