async def test_config_flow_user_step_success_claimed(hass: HomeAssistant) -> None:
    """Test user step where device is already claimed."""
    mock_client = MagicMock()
    mock_client.authenticate = AsyncMock(return_value=True)
    mock_client.recordNumber = TEST_RECORD_NUMBER
    mock_client.recordName = TEST_RECORD_NAME

    with patch(
        "homeassistant.components.energyid.config_flow.WebhookClient",
        return_value=mock_client,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_PROVISIONING_KEY: TEST_PROVISIONING_KEY,
                CONF_PROVISIONING_SECRET: TEST_PROVISIONING_SECRET,
            },
        )
        await hass.async_block_till_done()

        assert result2["type"] is FlowResultType.CREATE_ENTRY
        assert result2["title"] == TEST_RECORD_NAME
        assert result2["data"][CONF_PROVISIONING_KEY] == TEST_PROVISIONING_KEY
        assert result2["data"][CONF_PROVISIONING_SECRET] == TEST_PROVISIONING_SECRET
        assert result2["description"] == "add_sensor_mapping_hint"

        # Check unique_id is set correctly
        entry = hass.config_entries.async_get_entry(result2["result"].entry_id)
        # For initially claimed devices, unique_id should be the device_id, not record_number
        assert entry.unique_id.startswith("homeassistant_eid_")
        assert CONF_DEVICE_ID in entry.data
        assert entry.data[CONF_DEVICE_ID] == entry.unique_id