async def test_ssdp_already_configured(hass: HomeAssistant) -> None:
    """Test starting a flow from discovery when already configured."""
    with patch(
        "homeassistant.components.samsungtv.bridge.SamsungTVWSBridge.async_device_info",
        return_value=MOCK_DEVICE_INFO,
    ):
        # entry was added
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=MOCK_USER_DATA
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        entry = result["result"]
        assert entry.data[CONF_MANUFACTURER] == DEFAULT_MANUFACTURER
        assert entry.data[CONF_MODEL] == "fake_model"
        assert entry.unique_id == "123"

        # failed as already configured
        result2 = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_SSDP}, data=MOCK_SSDP_DATA
        )
        assert result2["type"] is FlowResultType.ABORT
        assert result2["reason"] == RESULT_ALREADY_CONFIGURED

        # check updated device info
        assert entry.unique_id == "123"