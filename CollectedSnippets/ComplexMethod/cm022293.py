async def test_user_step_cannot_connect(
    hass: HomeAssistant,
    mock_desk_api: MagicMock,
    exception: Exception,
    expected_error: str,
) -> None:
    """Test user step with a cannot connect error."""
    with patch(
        "homeassistant.components.idasen_desk.config_flow.async_discovered_service_info",
        return_value=[IDASEN_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    default_connect_side_effect = mock_desk_api.connect.side_effect
    mock_desk_api.connect.side_effect = exception

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_ADDRESS: IDASEN_DISCOVERY_INFO.address,
        },
    )
    await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "user"
    assert result2["errors"] == {"base": expected_error}

    mock_desk_api.connect.side_effect = default_connect_side_effect
    with patch(
        "homeassistant.components.idasen_desk.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                CONF_ADDRESS: IDASEN_DISCOVERY_INFO.address,
            },
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == IDASEN_DISCOVERY_INFO.name
    assert result3["data"] == {
        CONF_ADDRESS: IDASEN_DISCOVERY_INFO.address,
    }
    assert result3["result"].unique_id == IDASEN_DISCOVERY_INFO.address
    assert len(mock_setup_entry.mock_calls) == 1