async def test_manual(hass: HomeAssistant) -> None:
    """Test manually setup."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]

    # Cannot connect (timeout)
    with (
        _patch_discovery(no_device=True),
        _patch_config_flow_try_connect(no_device=True),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: IP_ADDRESS}
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "user"
    assert result2["errors"] == {"base": "cannot_connect"}

    # Success
    with (
        _patch_discovery(),
        _patch_config_flow_try_connect(),
        patch(f"{MODULE}.async_setup", return_value=True),
        patch(f"{MODULE}.async_setup_entry", return_value=True),
    ):
        result4 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: IP_ADDRESS}
        )
        await hass.async_block_till_done()
    assert result4["type"] is FlowResultType.CREATE_ENTRY
    assert result4["title"] == DEFAULT_ENTRY_TITLE
    assert result4["data"] == {
        CONF_HOST: IP_ADDRESS,
    }

    # Duplicate
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with (
        _patch_discovery(no_device=True),
        _patch_config_flow_try_connect(no_device=True),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: IP_ADDRESS}
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "already_configured"