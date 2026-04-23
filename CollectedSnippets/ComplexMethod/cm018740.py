async def test_zeroconf_empty_unique_id_uses_serial(hass: HomeAssistant) -> None:
    """Test zeroconf flow if printer lacks (empty) unique identification with serial fallback."""
    fixture = await hass.async_add_executor_job(
        load_fixture, "ipp/printer_without_uuid.json"
    )
    mock_printer_without_uuid = Printer.from_dict(json.loads(fixture))
    mock_printer_without_uuid.unique_id = None

    discovery_info = dataclasses.replace(MOCK_ZEROCONF_IPP_SERVICE_INFO)
    discovery_info.properties = {
        **MOCK_ZEROCONF_IPP_SERVICE_INFO.properties,
        "UUID": "",
    }
    with patch(
        "homeassistant.components.ipp.config_flow.IPP", autospec=True
    ) as ipp_mock:
        client = ipp_mock.return_value
        client.printer.return_value = mock_printer_without_uuid
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
    assert result["data"][CONF_UUID] == ""

    assert result["result"]
    assert result["result"].unique_id == "555534593035345555"