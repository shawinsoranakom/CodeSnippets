async def test_reauth_flow_preserves_non_credential_fields(
    hass: HomeAssistant,
    mock_bsblan: MagicMock,
) -> None:
    """Test reauth flow preserves non-credential fields using data_updates."""
    # Create a config entry with additional custom fields that should be preserved
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "127.0.0.1",
            CONF_PORT: 80,
            CONF_PASSKEY: "old_key",
            CONF_USERNAME: "old_user",
            CONF_PASSWORD: "old_pass",
            # Add some custom fields that should be preserved
            "custom_field": "should_be_preserved",
            "another_field": 42,
        },
        unique_id="00:80:41:19:69:90",
    )
    entry.add_to_hass(hass)

    # Start reauth flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": SOURCE_REAUTH,
            "entry_id": entry.entry_id,
        },
    )

    # Submit with only new credentials
    result = await _configure_flow(
        hass,
        result["flow_id"],
        {
            CONF_PASSKEY: "new_key",
            CONF_USERNAME: "new_user",
            CONF_PASSWORD: "new_pass",
        },
    )

    _assert_abort_result(result, "reauth_successful")

    # Verify that only the provided fields were updated, others preserved
    assert entry.data[CONF_PASSKEY] == "new_key"  # Updated
    assert entry.data[CONF_USERNAME] == "new_user"  # Updated
    assert entry.data[CONF_PASSWORD] == "new_pass"  # Updated

    # These fields should remain unchanged (preserved by data_updates)
    assert entry.data[CONF_HOST] == "127.0.0.1"
    assert entry.data[CONF_PORT] == 80
    assert entry.data["custom_field"] == "should_be_preserved"
    assert entry.data["another_field"] == 42