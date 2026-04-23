async def test_form_cannot_connect(
    hass: HomeAssistant, mock_pytouchline: MagicMock
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    # The config flow runs validation in a thread executor.
    # If `get_number_of_devices` fails, validation fails too.
    mock_pytouchline.get_number_of_devices.side_effect = ConnectionError

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=TEST_DATA,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    # "Fix" the problem, and try again.
    mock_pytouchline.get_number_of_devices.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=TEST_DATA,
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TEST_HOST
    assert result["data"] == TEST_DATA
    assert result["result"].unique_id == TEST_UNIQUE_ID