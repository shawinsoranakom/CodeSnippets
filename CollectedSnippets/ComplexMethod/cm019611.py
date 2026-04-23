async def test_addon_not_installed_failures(
    hass: HomeAssistant,
    supervisor: MagicMock,
    addon_not_installed: AsyncMock,
    addon_info: AsyncMock,
    install_addon: AsyncMock,
) -> None:
    """Test add-on install failure."""
    install_addon.side_effect = SupervisorError()

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "on_supervisor"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"use_addon": True}
    )

    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "install_addon"

    # Make sure the flow continues when the progress task is done.
    await hass.async_block_till_done()
    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert install_addon.call_args == call("core_matter_server")
    assert addon_info.call_count == 0
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "addon_install_failed"