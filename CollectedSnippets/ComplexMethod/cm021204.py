async def test_advanced_form_supervisor(hass: HomeAssistant) -> None:
    """Show advanced form when docker source is selected."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER, "show_advanced_options": True},
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_VERSION_SOURCE: VERSION_SOURCE_VERSIONS},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "version_source"

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "version_source"

    with patch(
        "homeassistant.components.version.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_CHANNEL: "Dev", CONF_IMAGE: "odroid-n2", CONF_BOARD: "ODROID N2"},
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"{VERSION_SOURCE_VERSIONS} Dev"
    assert result["data"] == {
        **DEFAULT_CONFIGURATION,
        CONF_IMAGE: "odroid-n2",
        CONF_BOARD: "ODROID N2",
        CONF_CHANNEL: HaVersionChannel.DEV,
        CONF_SOURCE: HaVersionSource.SUPERVISOR,
        CONF_VERSION_SOURCE: VERSION_SOURCE_VERSIONS,
    }
    assert len(mock_setup_entry.mock_calls) == 1