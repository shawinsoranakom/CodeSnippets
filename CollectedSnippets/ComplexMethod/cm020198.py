async def test_discovery(
    hass: HomeAssistant,
    discovery_data: SsdpServiceInfo,
    discovery_data_bedroom: SsdpServiceInfo,
    controller: MockHeos,
    system: HeosSystem,
) -> None:
    """Test discovery shows form to confirm, then creates entry."""
    # Single discovered, selects preferred host, shows confirm
    controller.get_system_info.return_value = system
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_SSDP}, data=discovery_data_bedroom
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm_discovery"
    assert controller.connect.call_count == 1
    assert controller.get_system_info.call_count == 1
    assert controller.disconnect.call_count == 1

    # Subsequent discovered hosts abort.
    subsequent_result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_SSDP}, data=discovery_data
    )
    assert subsequent_result["type"] is FlowResultType.ABORT
    assert subsequent_result["reason"] == "already_in_progress"

    # Confirm set up
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == DOMAIN
    assert result["title"] == "HEOS System"
    assert result["data"] == {CONF_HOST: "127.0.0.1"}