async def test_recovery_after_error(
    hass: HomeAssistant,
    exception_type: Exception,
    expected_error: str,
    mock_pterodactyl: Generator[AsyncMock],
) -> None:
    """Test recovery after an error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    mock_pterodactyl.client.servers.list_servers.side_effect = exception_type

    result = await hass.config_entries.flow.async_configure(
        flow_id=result["flow_id"],
        user_input=TEST_USER_INPUT,
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": expected_error}

    mock_pterodactyl.reset_mock(side_effect=True)

    result = await hass.config_entries.flow.async_configure(
        flow_id=result["flow_id"], user_input=TEST_USER_INPUT
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TEST_URL
    assert result["data"] == TEST_USER_INPUT