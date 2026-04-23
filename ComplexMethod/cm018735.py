async def test_zeroconf_empty_unique_id(
    hass: HomeAssistant,
    mock_ipp_config_flow: MagicMock,
) -> None:
    """Test zeroconf flow if printer lacks (empty) unique identification."""
    printer = mock_ipp_config_flow.printer.return_value
    printer.unique_id = None

    discovery_info = dataclasses.replace(MOCK_ZEROCONF_IPP_SERVICE_INFO)
    discovery_info.properties = {
        **MOCK_ZEROCONF_IPP_SERVICE_INFO.properties,
        "UUID": "",
    }
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=discovery_info,
    )

    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "192.168.1.31", CONF_BASE_PATH: "/ipp/print"},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "EPSON XP-6000 Series"

    assert result["data"]
    assert result["data"][CONF_HOST] == "192.168.1.31"
    assert result["data"][CONF_UUID] == "cfe92100-67c4-11d4-a45f-f8d027761251"

    assert result["result"]
    assert result["result"].unique_id == "cfe92100-67c4-11d4-a45f-f8d027761251"