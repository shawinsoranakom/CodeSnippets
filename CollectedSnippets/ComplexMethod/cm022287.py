async def test_user_exception_user_step(hass: HomeAssistant) -> None:
    """Test we handle Exception errors in user step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(
        "homeassistant.components.nanoleaf.config_flow.Nanoleaf",
        return_value=_mock_nanoleaf(authorize_error=Exception()),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: TEST_HOST,
            },
        )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "user"
    assert result2["errors"] == {"base": "unknown"}
    assert not result2["last_step"]

    with patch(
        "homeassistant.components.nanoleaf.config_flow.Nanoleaf",
        return_value=_mock_nanoleaf(),
    ) as mock_nanoleaf:
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: TEST_HOST,
            },
        )
        assert result3["step_id"] == "link"

        mock_nanoleaf.return_value.authorize.side_effect = Exception()

        result4 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        assert result4["type"] is FlowResultType.FORM
        assert result4["step_id"] == "link"
        assert result4["errors"] == {"base": "unknown"}

        mock_nanoleaf.return_value.authorize.side_effect = None
        mock_nanoleaf.return_value.get_info.side_effect = Exception()
        result5 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result5["type"] is FlowResultType.ABORT
    assert result5["reason"] == "unknown"