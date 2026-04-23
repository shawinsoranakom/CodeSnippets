async def test_full_zeroconf_flow_implementation(
    hass: HomeAssistant,
    mock_elgato: MagicMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test the zeroconf flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            hostname="example.local.",
            name="mock_name",
            port=9123,
            properties={"id": "AA:BB:CC:DD:EE:FF"},
            type="mock_type",
        ),
    )

    assert result["description_placeholders"] == {"serial_number": "CN11A1A00001"}
    assert result["step_id"] == "zeroconf_confirm"
    assert result["type"] is FlowResultType.FORM

    progress = hass.config_entries.flow.async_progress()
    assert len(progress) == 1
    assert progress[0].get("flow_id") == result["flow_id"]
    assert "context" in progress[0]
    assert progress[0]["context"].get("confirm_only") is True

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY

    config_entry = result["result"]
    assert config_entry.unique_id == "CN11A1A00001"
    assert config_entry.data == {
        CONF_HOST: "127.0.0.1",
        CONF_MAC: "AA:BB:CC:DD:EE:FF",
    }
    assert not config_entry.options

    assert len(mock_setup_entry.mock_calls) == 1
    assert len(mock_elgato.info.mock_calls) == 1