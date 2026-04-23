async def test_user_config(
    hass: HomeAssistant, mock_setup_entry: MagicMock, mock_nextbus_lists: MagicMock
) -> None:
    """Test we get the form."""
    await setup.async_setup_component(hass, "persistent_notification", {})
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "agency"

    # Select agency
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_AGENCY: "sfmta-cis",
        },
    )
    await hass.async_block_till_done()

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "route"

    # Select route
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_ROUTE: "F",
        },
    )
    await hass.async_block_till_done()

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "stop"

    # Select stop
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_STOP: "5184",
        },
    )
    await hass.async_block_till_done()

    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("data") == {
        "agency": "sfmta-cis",
        "route": "F",
        "stop": "5184",
    }

    assert len(mock_setup_entry.mock_calls) == 1