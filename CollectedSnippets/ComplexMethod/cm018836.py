async def test_migrate_from_version_1_success(hass: HomeAssistant) -> None:
    """Test successful config migration from version 1."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        unique_id=UNIQUE_ID,
        data=CONFIG_V1,
    )

    # Mock the migrate token endpoint response
    with patch(
        "homeassistant.components.teslemetry.Teslemetry.migrate_to_oauth",
        new_callable=AsyncMock,
    ) as mock_migrate:
        mock_migrate.return_value = {
            "token": {
                "access_token": "migrated_token",
                "token_type": "Bearer",
                "refresh_token": "migrated_refresh_token",
                "expires_in": 3600,
                "expires_at": time.time() + 3600,
            }
        }

        mock_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_entry.entry_id)
        await hass.async_block_till_done()

        mock_migrate.assert_called_once_with(CLIENT_ID, hass.config.location_name)

    assert mock_entry is not None
    assert mock_entry.version == 2
    # Verify data was converted to OAuth format
    assert "token" in mock_entry.data
    assert mock_entry.data["token"]["access_token"] == "migrated_token"
    assert mock_entry.data["token"]["refresh_token"] == "migrated_refresh_token"
    # Verify auth_implementation was added for OAuth2 flow compatibility
    assert mock_entry.data["auth_implementation"] == DOMAIN
    assert mock_entry.state is ConfigEntryState.LOADED