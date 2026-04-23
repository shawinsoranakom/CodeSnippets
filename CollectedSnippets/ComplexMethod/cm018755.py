async def test_flow_fails(
    hass: HomeAssistant,
    flow_id: str,
    error: Exception,
    message: str,
    mock_setup_entry,
    mock_flexit_bacnet,
) -> None:
    """Test that we return 'cannot_connect' error when attempting to connect to an incorrect IP address.

    The flexit_bacnet library raises asyncio.exceptions.TimeoutError in that scenario.
    """
    mock_flexit_bacnet.update.side_effect = error
    result = await hass.config_entries.flow.async_configure(
        flow_id,
        {
            CONF_IP_ADDRESS: "1.1.1.1",
            CONF_DEVICE_ID: 2,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": message}
    assert len(mock_setup_entry.mock_calls) == 0

    # ensure that user can recover from this error
    mock_flexit_bacnet.update.side_effect = None
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_IP_ADDRESS: "1.1.1.1",
            CONF_DEVICE_ID: 2,
        },
    )

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Device Name"
    assert result2["context"]["unique_id"] == "0000-0001"
    assert result2["data"] == {
        CONF_IP_ADDRESS: "1.1.1.1",
        CONF_DEVICE_ID: 2,
    }
    assert len(mock_setup_entry.mock_calls) == 1