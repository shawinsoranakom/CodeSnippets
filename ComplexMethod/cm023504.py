async def test_form_exception(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    exception: Exception,
    expected_error_key: str,
) -> None:
    """Test handling an exception and then recovering on the second attempt."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.aosmith.config_flow.AOSmithAPIClient.get_devices",
        side_effect=exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT,
        )
        assert result2["type"] is FlowResultType.FORM
        assert result2["errors"] == {"base": expected_error_key}

    with patch(
        "homeassistant.components.aosmith.config_flow.AOSmithAPIClient.get_devices",
        return_value=[],
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            FIXTURE_USER_INPUT,
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == FIXTURE_USER_INPUT[CONF_EMAIL]
    assert result3["data"] == FIXTURE_USER_INPUT
    assert len(mock_setup_entry.mock_calls) == 1