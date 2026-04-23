async def test_async_step_user_takes_precedence_over_discovery(
    hass: HomeAssistant,
) -> None:
    """Test manual setup takes precedence over discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=GVH5177_SERVICE_INFO,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"

    with patch(
        "homeassistant.components.govee_ble.config_flow.async_discovered_service_info",
        return_value=[GVH5177_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
        assert result["type"] is FlowResultType.FORM

    with patch(
        "homeassistant.components.govee_ble.async_setup_entry", return_value=True
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"address": "4125DDBA-2774-4851-9889-6AADDD4CAC3D"},
        )
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "H5177 2EC8"
    assert result2["data"] == {CONF_DEVICE_TYPE: "H5177"}
    assert result2["result"].unique_id == "4125DDBA-2774-4851-9889-6AADDD4CAC3D"

    # Verify the original one was aborted
    assert not hass.config_entries.flow.async_progress(DOMAIN)