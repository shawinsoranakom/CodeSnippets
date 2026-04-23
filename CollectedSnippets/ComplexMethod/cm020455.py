async def test_manual_recoverable_error(
    hass: HomeAssistant, mock_discovery: AbstractContextManager, error_reason: str
) -> None:
    """Test manual with a recoverable error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "manual"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual"

    with mock_discovery:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_HOST: RECEIVER_INFO_2.host}
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual"
    assert result["errors"] == {"base": error_reason}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: RECEIVER_INFO_2.host}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "configure_receiver"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            OPTION_VOLUME_RESOLUTION: 200,
            OPTION_INPUT_SOURCES: ["TV"],
            OPTION_LISTENING_MODES: ["THX"],
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_HOST] == RECEIVER_INFO_2.host
    assert result["result"].unique_id == RECEIVER_INFO_2.identifier
    assert result["title"] == RECEIVER_INFO_2.model_name