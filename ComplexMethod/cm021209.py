async def test_flow_user_in_progress(hass: HomeAssistant) -> None:
    """Test user flow with no available devices."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
    )
    assert result
    assert result.get("type") is FlowResultType.FORM
    assert not result.get("errors")
    assert result.get("flow_id")
    assert result.get("step_id") == "user"

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
    )
    assert result
    assert result.get("type") is FlowResultType.ABORT
    assert result.get("reason") == "already_in_progress"