async def test_communication_error_on_device_info(
    hass: HomeAssistant, mock_prana_api
) -> None:
    """Communication errors when fetching device info surface as form errors."""

    # Setting an invalid device info, for abort the flow
    device_info_invalid = await async_load_fixture(hass, "device_info_invalid.json")
    mock_prana_api.get_device_info.return_value = SimpleNamespace(**device_info_invalid)
    mock_prana_api.get_device_info.side_effect = None
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: "192.168.1.50"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "invalid_device"

    # Simulating a communication error
    device_info = await async_load_fixture(hass, "device_info.json")
    mock_prana_api.get_device_info.return_value = SimpleNamespace(**device_info)
    mock_prana_api.get_device_info.side_effect = PranaCommunicationError(
        "Network error"
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: "192.168.1.50"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert "invalid_device_or_unreachable" in result["errors"].values()

    # Now simulating a successful fetch, without aborting
    mock_prana_api.get_device_info.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: "192.168.1.50"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == device_info["label"]
    assert result["result"].unique_id == device_info["manufactureId"]
    assert result["result"].data == {CONF_HOST: "192.168.1.50"}