async def test_async_step_user_takes_precedence_over_discovery(
    hass: HomeAssistant,
) -> None:
    """Test manual setup takes precedence over discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=KEGTRON_KT100_SERVICE_INFO,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"

    with patch(
        "homeassistant.components.kegtron.config_flow.async_discovered_service_info",
        return_value=[KEGTRON_KT100_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
        assert result["type"] is FlowResultType.FORM

    with patch("homeassistant.components.kegtron.async_setup_entry", return_value=True):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"address": "D0:CF:5E:5C:9B:75"},
        )
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Kegtron KT-100 9B75"
    assert result2["data"] == {}
    assert result2["result"].unique_id == "D0:CF:5E:5C:9B:75"

    # Verify the original one was aborted
    assert not hass.config_entries.flow.async_progress(DOMAIN)