async def test_form_exceptions(
    hass: HomeAssistant,
    exception: Exception,
    error: dict[str, str],
    mock_fyta_connector: AsyncMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test we can handle Form exceptions."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_fyta_connector.login.side_effect = exception

    # tests with connection error
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == error

    mock_fyta_connector.login.side_effect = None

    # tests with all information provided
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == USERNAME
    assert result["data"][CONF_USERNAME] == USERNAME
    assert result["data"][CONF_PASSWORD] == PASSWORD
    assert result["data"][CONF_ACCESS_TOKEN] == ACCESS_TOKEN
    assert result["data"][CONF_EXPIRATION] == EXPIRATION

    assert len(mock_setup_entry.mock_calls) == 1