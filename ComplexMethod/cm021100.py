async def test_full_user_flow(hass: HomeAssistant) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"

    with (
        patch(
            "homeassistant.components.p1_monitor.config_flow.P1Monitor.settings"
        ) as mock_p1monitor,
        patch(
            "homeassistant.components.p1_monitor.async_setup_entry", return_value=True
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "example.com", CONF_PORT: 80},
        )

    assert result2.get("type") is FlowResultType.CREATE_ENTRY
    assert result2.get("title") == "P1 Monitor"
    assert result2.get("data") == {CONF_HOST: "example.com", CONF_PORT: 80}
    assert isinstance(result2["data"][CONF_PORT], int)

    assert len(mock_setup_entry.mock_calls) == 1
    assert len(mock_p1monitor.mock_calls) == 1