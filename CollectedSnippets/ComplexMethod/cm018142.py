async def test_zeroconf_flow_errors(
    hass: HomeAssistant,
    mock_stream_magic_client: AsyncMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test zeroconf flow."""
    mock_stream_magic_client.connect.side_effect = StreamMagicError
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY,
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "cannot_connect"

    mock_stream_magic_client.connect.side_effect = None

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "discovery_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Cambridge Audio CXNv2"
    assert result["data"] == {
        CONF_HOST: "192.168.20.218",
    }
    assert result["result"].unique_id == "0020c2d8"