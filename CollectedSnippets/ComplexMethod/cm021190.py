async def test_full_flow_with_authentication_error(
    hass: HomeAssistant,
    mock_pvoutput: MagicMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test the full user configuration flow with incorrect API key.

    This tests tests a full config flow, with a case the user enters an invalid
    PVOutput API key, but recovers by entering the correct one.
    """
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"

    mock_pvoutput.system.side_effect = PVOutputAuthenticationError
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_SYSTEM_ID: 12345,
            CONF_API_KEY: "invalid",
        },
    )

    assert result2.get("type") is FlowResultType.FORM
    assert result2.get("step_id") == "user"
    assert result2.get("errors") == {"base": "invalid_auth"}

    assert len(mock_setup_entry.mock_calls) == 0
    assert len(mock_pvoutput.system.mock_calls) == 1

    mock_pvoutput.system.side_effect = None
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        user_input={
            CONF_SYSTEM_ID: 12345,
            CONF_API_KEY: "tadaaa",
        },
    )

    assert result3.get("type") is FlowResultType.CREATE_ENTRY
    assert result3.get("title") == "12345"
    assert result3.get("data") == {
        CONF_SYSTEM_ID: 12345,
        CONF_API_KEY: "tadaaa",
    }

    assert len(mock_setup_entry.mock_calls) == 1
    assert len(mock_pvoutput.system.mock_calls) == 2