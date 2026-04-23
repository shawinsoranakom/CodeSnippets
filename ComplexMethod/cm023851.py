async def test_connection_error(
    hass: HomeAssistant,
    mock_twentemilieu: MagicMock,
) -> None:
    """Test we show user form on Twente Milieu connection error."""
    mock_twentemilieu.unique_id.side_effect = TwenteMilieuConnectionError

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_POST_CODE: "1234AB",
            CONF_HOUSE_NUMBER: "1",
            CONF_HOUSE_LETTER: "A",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}

    # Recover from error
    mock_twentemilieu.unique_id.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_POST_CODE: "1234AB",
            CONF_HOUSE_NUMBER: "1",
            CONF_HOUSE_LETTER: "A",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY

    config_entry = result["result"]
    assert config_entry.unique_id == "12345"
    assert config_entry.data == {
        CONF_HOUSE_LETTER: "A",
        CONF_HOUSE_NUMBER: "1",
        CONF_ID: 12345,
        CONF_POST_CODE: "1234AB",
    }
    assert not config_entry.options