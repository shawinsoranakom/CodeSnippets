async def test_bluetooth_step_success(
    hass: HomeAssistant, mock_desk_api: MagicMock
) -> None:
    """Test bluetooth step success path."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=IDASEN_DISCOVERY_INFO,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.idasen_desk.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ADDRESS: IDASEN_DISCOVERY_INFO.address,
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == IDASEN_DISCOVERY_INFO.name
    assert result2["data"] == {
        CONF_ADDRESS: IDASEN_DISCOVERY_INFO.address,
    }
    assert result2["result"].unique_id == IDASEN_DISCOVERY_INFO.address
    assert len(mock_setup_entry.mock_calls) == 1
    mock_desk_api.connect.assert_called_with(ANY, retry=False)