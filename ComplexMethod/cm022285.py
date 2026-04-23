async def test_user_unavailable_user_step_link_step(hass: HomeAssistant) -> None:
    """Test we handle Unavailable in user and link step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(
        "homeassistant.components.nanoleaf.config_flow.Nanoleaf.authorize",
        side_effect=Unavailable,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: TEST_HOST,
            },
        )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "user"
    assert result2["errors"] == {"base": "cannot_connect"}
    assert not result2["last_step"]

    with patch(
        "homeassistant.components.nanoleaf.config_flow.Nanoleaf.authorize",
        return_value=None,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: TEST_HOST,
            },
        )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "link"

    with patch(
        "homeassistant.components.nanoleaf.config_flow.Nanoleaf.authorize",
        side_effect=Unavailable,
    ):
        result3 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result3["type"] is FlowResultType.ABORT
    assert result3["reason"] == "cannot_connect"