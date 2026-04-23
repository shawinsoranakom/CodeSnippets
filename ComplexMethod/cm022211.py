async def test_dhcp_flow(
    hass: HomeAssistant,
    dhcp_service_info: DhcpServiceInfo,
    mock_airthings_token: AsyncMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test the DHCP discovery flow."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=dhcp_service_info,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_DATA,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Airthings"
    assert result["data"] == TEST_DATA
    assert result["result"].unique_id == TEST_DATA[CONF_ID]
    assert len(mock_setup_entry.mock_calls) == 1