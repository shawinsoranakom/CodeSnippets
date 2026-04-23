async def test_step_user_form(
    hass: HomeAssistant,
    mock_watergate_client: Generator[AsyncMock],
    mock_webhook_id_generation: Generator[None],
    user_input: dict[str, str],
) -> None:
    """Test checking if registration form works end to end."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert CONF_IP_ADDRESS in result["data_schema"].schema

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Sonic"
    assert result["data"] == {**user_input, CONF_WEBHOOK_ID: MOCK_WEBHOOK_ID}
    assert result["result"].unique_id == DEFAULT_SERIAL_NUMBER