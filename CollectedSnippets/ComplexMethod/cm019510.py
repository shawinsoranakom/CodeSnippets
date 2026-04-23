async def test_step_user_form_with_exception(
    hass: HomeAssistant,
    mock_watergate_client: Generator[AsyncMock],
    user_input: dict[str, str],
    client_result: AsyncMock,
    mock_webhook_id_generation: Generator[None],
) -> None:
    """Test checking if errors will be displayed when Exception is thrown while checking device state."""
    mock_watergate_client.async_get_device_state = client_result

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"][CONF_IP_ADDRESS] == "cannot_connect"

    mock_watergate_client.async_get_device_state = AsyncMock(
        return_value=DEFAULT_DEVICE_STATE
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Sonic"
    assert result["data"] == {**user_input, CONF_WEBHOOK_ID: MOCK_WEBHOOK_ID}