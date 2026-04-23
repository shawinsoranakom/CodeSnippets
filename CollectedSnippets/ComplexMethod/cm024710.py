async def test_multiple_different_devices_allowed(hass: HomeAssistant) -> None:
    """Test that multiple config entries with different device_ids are allowed."""
    # Create existing entry with one device_id
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="homeassistant_eid_device_1",
        data={
            CONF_PROVISIONING_KEY: "key1",
            CONF_PROVISIONING_SECRET: "secret1",
            CONF_DEVICE_ID: "homeassistant_eid_device_1",
            CONF_DEVICE_NAME: "Device 1",
        },
    )
    entry.add_to_hass(hass)

    mock_client = MagicMock()
    mock_client.authenticate = AsyncMock(return_value=True)
    mock_client.recordNumber = TEST_RECORD_NUMBER
    mock_client.recordName = TEST_RECORD_NAME

    with patch(
        "homeassistant.components.energyid.config_flow.WebhookClient",
        return_value=mock_client,
    ):
        # Check initial result
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"

        # Configure with different credentials (will create different device_id)
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_PROVISIONING_KEY: "key2",
                CONF_PROVISIONING_SECRET: "secret2",
            },
        )

        # Should succeed because device_id will be different
        assert result2["type"] is FlowResultType.CREATE_ENTRY
        assert result2["title"] == TEST_RECORD_NAME
        assert result2["data"][CONF_PROVISIONING_KEY] == "key2"
        assert result2["data"][CONF_PROVISIONING_SECRET] == "secret2"
        assert result2["description"] == "add_sensor_mapping_hint"

        # Verify unique_id is set
        new_entry = hass.config_entries.async_get_entry(result2["result"].entry_id)
        assert new_entry.unique_id is not None
        assert new_entry.unique_id != entry.unique_id