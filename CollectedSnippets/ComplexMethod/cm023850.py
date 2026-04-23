async def test_invalid_address(
    hass: HomeAssistant,
    mock_twentemilieu: MagicMock,
) -> None:
    """Test full user flow when the user enters an incorrect address.

    This tests also tests if the user recovers from it by entering a valid
    address in the second attempt.
    """
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    mock_twentemilieu.unique_id.side_effect = TwenteMilieuAddressError
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_POST_CODE: "1234",
            CONF_HOUSE_NUMBER: "1",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "invalid_address"}

    mock_twentemilieu.unique_id.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_POST_CODE: "1234AB",
            CONF_HOUSE_NUMBER: "1",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY

    config_entry = result["result"]
    assert config_entry.unique_id == "12345"
    assert config_entry.data == {
        CONF_HOUSE_LETTER: None,
        CONF_HOUSE_NUMBER: "1",
        CONF_ID: 12345,
        CONF_POST_CODE: "1234AB",
    }
    assert not config_entry.options