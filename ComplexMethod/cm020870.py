async def test_zeroconf_confirm_flow_success(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, mock_homevolt_client: MagicMock
) -> None:
    """Test zeroconf flow shows confirm step before creating entry."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=DISCOVERY_INFO,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "zeroconf_confirm"
    assert result["description_placeholders"] == {"host": "192.168.1.123"}

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Homevolt"
    assert result["data"] == {CONF_HOST: "192.168.1.123", CONF_PASSWORD: None}
    assert result["result"].unique_id == "40580137858664"
    assert len(mock_setup_entry.mock_calls) == 1