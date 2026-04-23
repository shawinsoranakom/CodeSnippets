async def test_discovery_but_cannot_connect(hass: HomeAssistant) -> None:
    """Test we can discover the device but we cannot connect."""
    with _patch_discovery(), _patch_config_flow_try_connect(no_device=True):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        await hass.async_block_till_done()
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"
        assert not result["errors"]

        result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        await hass.async_block_till_done()
        assert result2["type"] is FlowResultType.FORM
        assert result2["step_id"] == "pick_device"
        assert not result2["errors"]

        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_DEVICE: SERIAL},
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.ABORT
    assert result3["reason"] == "cannot_connect"