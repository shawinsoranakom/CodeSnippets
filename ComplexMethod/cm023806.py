async def test_setup_via_discovery_cannot_connect(hass: HomeAssistant) -> None:
    """Test setting up via discovery and we fail to connect to the discovered device."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]

    with _patch_discovery():
        result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "pick_device"
    assert not result2["errors"]

    with (
        patch(
            "homeassistant.components.wiz.wizlight.getBulbConfig",
            side_effect=WizLightTimeOutError,
        ),
        _patch_discovery(),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_DEVICE: FAKE_MAC},
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.ABORT
    assert result3["reason"] == "cannot_connect"