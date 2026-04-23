async def test_ssdp_update_mac(hass: HomeAssistant) -> None:
    """Ensure that MAC address is correctly updated from SSDP."""
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
        assert entry.data[CONF_MAC] is None
        assert entry.data[CONF_PORT] == 8002
        assert entry.unique_id == "123"

    device_info = deepcopy(MOCK_DEVICE_INFO)
    device_info["device"]["wifiMac"] = "none"
    with patch(
        "homeassistant.components.samsungtv.bridge.SamsungTVWSBridge.async_device_info",
        return_value=device_info,
    ):
        # Updated
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_SSDP}, data=MOCK_SSDP_DATA
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == RESULT_ALREADY_CONFIGURED

        # ensure mac wasn't updated with "none"
        assert entry.data[CONF_MAC] is None
        assert entry.unique_id == "123"

    device_info = deepcopy(MOCK_DEVICE_INFO)
    device_info["device"]["wifiMac"] = "aa:bb:cc:dd:ee:ff"
    with patch(
        "homeassistant.components.samsungtv.bridge.SamsungTVWSBridge.async_device_info",
        return_value=device_info,
    ):
        # Updated
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_SSDP}, data=MOCK_SSDP_DATA
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == RESULT_ALREADY_CONFIGURED

        # ensure mac was updated with new wifiMac value
        assert entry.data[CONF_MAC] == "aa:bb:cc:dd:ee:ff"
        assert entry.unique_id == "123"