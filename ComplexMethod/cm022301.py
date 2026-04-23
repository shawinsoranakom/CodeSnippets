async def test_async_step_user_takes_precedence_over_discovery(
    hass: HomeAssistant,
) -> None:
    """Test manual setup takes precedence over discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=T9146_SERVICE_INFO,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"

    with patch(
        "homeassistant.components.eufylife_ble.config_flow.async_discovered_service_info",
        return_value=[T9146_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
        assert result["type"] is FlowResultType.FORM

    with patch(
        "homeassistant.components.eufylife_ble.async_setup_entry", return_value=True
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"address": "11:22:33:44:55:66"},
        )
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Smart Scale C1"
    assert result2["data"] == {"model": "eufy T9146"}
    assert result2["result"].unique_id == "11:22:33:44:55:66"

    # Verify the original one was aborted
    assert not hass.config_entries.flow.async_progress(DOMAIN)