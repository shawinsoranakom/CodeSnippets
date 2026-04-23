async def test_form(hass: HomeAssistant) -> None:
    """Test we get the form."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    mock_value_step_rm = {
        "relay_1": "bistable",  # Mocking a single relay board instance.
    }

    with patch(
        "homeassistant.components.progettihwsw.config_flow.ProgettiHWSWAPI.check_board",
        return_value=mock_value_step_user,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "", CONF_PORT: 80},
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "relay_modes"
    assert result2["errors"] == {}

    with patch(
        "homeassistant.components.progettihwsw.async_setup_entry",
        return_value=True,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            mock_value_step_rm,
        )

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["data"]
    assert result3["data"]["title"] == "1R & 1IN Board"
    assert result3["data"]["is_old"] is False
    assert result3["data"]["relay_count"] == result3["data"]["input_count"] == 1