async def test_flow_errors(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_smile_config_flow: MagicMock,
    side_effect: Exception,
    reason: str,
) -> None:
    """Test we handle each exception error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("errors") == {}
    assert result.get("step_id") == "user"
    assert "flow_id" in result

    mock_smile_config_flow.connect.side_effect = side_effect

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: TEST_HOST, CONF_PASSWORD: TEST_PASSWORD},
    )

    assert result2.get("type") is FlowResultType.FORM
    assert result2.get("errors") == {"base": reason}
    assert result2.get("step_id") == "user"

    assert len(mock_setup_entry.mock_calls) == 0
    assert len(mock_smile_config_flow.connect.mock_calls) == 1

    mock_smile_config_flow.connect.side_effect = None
    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: TEST_HOST, CONF_PASSWORD: TEST_PASSWORD},
    )

    assert result3.get("type") is FlowResultType.CREATE_ENTRY
    assert result3.get("title") == "Test Smile Name"
    assert result3.get("data") == {
        CONF_HOST: TEST_HOST,
        CONF_PASSWORD: TEST_PASSWORD,
        CONF_PORT: DEFAULT_PORT,
        CONF_USERNAME: TEST_USERNAME,
    }

    assert len(mock_setup_entry.mock_calls) == 1
    assert len(mock_smile_config_flow.connect.mock_calls) == 2