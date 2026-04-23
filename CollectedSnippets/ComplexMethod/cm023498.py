async def test_async_step_user_with_found_devices_encryption(
    hass: HomeAssistant,
) -> None:
    """Test setup from service info cache with devices found, with encryption."""
    with patch(
        "homeassistant.components.bthome.config_flow.async_discovered_service_info",
        return_value=[TEMP_HUMI_ENCRYPTED_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result1 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"address": "54:48:E6:8F:80:A5"},
    )
    assert result1["type"] is FlowResultType.FORM
    assert result1["step_id"] == "get_encryption_key"

    with patch("homeassistant.components.bthome.async_setup_entry", return_value=True):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"bindkey": "231d39c1d7cc1ab1aee224cd096db932"},
        )

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "TEST DEVICE 80A5"
    assert result2["data"] == {"bindkey": "231d39c1d7cc1ab1aee224cd096db932"}
    assert result2["result"].unique_id == "54:48:E6:8F:80:A5"