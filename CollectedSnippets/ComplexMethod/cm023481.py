async def test_user_walkthrough(
    hass: HomeAssistant, toloclient: Mock, coordinator_toloclient: Mock
) -> None:
    """Test complete user flow with first wrong and then correct host."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    toloclient().get_status.side_effect = lambda *args, **kwargs: None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "127.0.0.2"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}

    toloclient().get_status.side_effect = lambda *args, **kwargs: object()

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "127.0.0.1"},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "TOLO Sauna"
    assert result["data"][CONF_HOST] == "127.0.0.1"