async def test_configure(hass: HomeAssistant) -> None:
    """Test receiver configure."""
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

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: RECEIVER_INFO.host}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "configure_receiver"
    assert result["description_placeholders"]["name"] == _receiver_display_name(
        RECEIVER_INFO
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            OPTION_VOLUME_RESOLUTION: 200,
            OPTION_INPUT_SOURCES: [],
            OPTION_LISTENING_MODES: ["THX"],
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "configure_receiver"
    assert result["errors"] == {OPTION_INPUT_SOURCES: "empty_input_source_list"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            OPTION_VOLUME_RESOLUTION: 200,
            OPTION_INPUT_SOURCES: ["TV"],
            OPTION_LISTENING_MODES: [],
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "configure_receiver"
    assert result["errors"] == {OPTION_LISTENING_MODES: "empty_listening_mode_list"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            OPTION_VOLUME_RESOLUTION: 200,
            OPTION_INPUT_SOURCES: ["TV"],
            OPTION_LISTENING_MODES: ["THX"],
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["options"] == {
        OPTION_VOLUME_RESOLUTION: 200,
        OPTION_MAX_VOLUME: OPTION_MAX_VOLUME_DEFAULT,
        OPTION_INPUT_SOURCES: {"12": "TV"},
        OPTION_LISTENING_MODES: {"04": "THX"},
    }