async def test_zeroconf_abort_anna_with_adam(hass: HomeAssistant) -> None:
    """Test we abort Anna discovery when an Adam is also discovered."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_ZEROCONF},
        data=TEST_DISCOVERY_ANNA,
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"

    flows_in_progress = hass.config_entries.flow._handler_progress_index[DOMAIN]
    assert len(flows_in_progress) == 1
    assert list(flows_in_progress)[0].product == "smile_thermo"

    # Discover Adam, Anna should be aborted and no longer present
    result2 = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_ZEROCONF},
        data=TEST_DISCOVERY_ADAM,
    )

    assert result2.get("type") is FlowResultType.FORM
    assert result2.get("step_id") == "user"

    flows_in_progress = hass.config_entries.flow._handler_progress_index[DOMAIN]
    assert len(flows_in_progress) == 1
    assert list(flows_in_progress)[0].product == "smile_open_therm"

    # Discover Anna again, Anna should be aborted directly
    result3 = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_ZEROCONF},
        data=TEST_DISCOVERY_ANNA,
    )
    assert result3.get("type") is FlowResultType.ABORT
    assert result3.get("reason") == "anna_with_adam"

    # Adam should still be there
    flows_in_progress = hass.config_entries.flow._handler_progress_index[DOMAIN]
    assert len(flows_in_progress) == 1
    assert list(flows_in_progress)[0].product == "smile_open_therm"