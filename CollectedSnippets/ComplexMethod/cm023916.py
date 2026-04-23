async def test_reconfigure_flow_no_machines(
    hass: HomeAssistant,
    mock_cloud_client: MagicMock,
    mock_config_entry: MockConfigEntry,
    discovered: list[BluetoothServiceInfo],
) -> None:
    """Testing reconfgure flow."""
    mock_config_entry.add_to_hass(hass)

    data = deepcopy(dict(mock_config_entry.data))
    result = await mock_config_entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    result = await __do_successful_user_step(hass, result, mock_cloud_client)

    with (
        patch(
            "homeassistant.components.lamarzocco.config_flow.async_discovered_service_info",
            return_value=discovered,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_MACHINE: "GS012345",
            },
        )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    assert mock_config_entry.title == "My LaMarzocco"
    assert CONF_MAC not in mock_config_entry.data
    assert dict(mock_config_entry.data) == data