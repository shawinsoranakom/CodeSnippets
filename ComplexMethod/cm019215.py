async def test_async_step_user_takes_precedence_over_discovery(
    hass: HomeAssistant,
) -> None:
    """Test manual setup takes precedence over discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=DKEY_DISCOVERY_INFO,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"

    with patch(
        "homeassistant.components.dormakaba_dkey.config_flow.async_discovered_service_info",
        return_value=[DKEY_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
        assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_ADDRESS: DKEY_DISCOVERY_INFO.address,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "associate"
    assert result["errors"] is None

    await _test_common_success(hass, result)

    # Verify the discovery flow was aborted
    assert not hass.config_entries.flow.async_progress(DOMAIN)