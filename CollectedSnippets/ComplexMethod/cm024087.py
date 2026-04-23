async def test_async_step_user_takes_precedence_over_discovery(
    hass: HomeAssistant,
) -> None:
    """Test manual setup takes precedence over discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=SPS_SERVICE_INFO,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"

    with patch(
        "homeassistant.components.inkbird.config_flow.async_discovered_service_info",
        return_value=[SPS_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
        assert result["type"] is FlowResultType.FORM

    with patch("homeassistant.components.inkbird.async_setup_entry", return_value=True):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"address": "61DE521B-F0BF-9F44-64D4-75BBE1738105"},
        )
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "IBS-TH 8105"
    assert result2["data"] == {CONF_DEVICE_TYPE: "IBS-TH"}
    assert result2["result"].unique_id == "61DE521B-F0BF-9F44-64D4-75BBE1738105"

    # Verify the original one was aborted
    assert not hass.config_entries.flow.async_progress(DOMAIN)