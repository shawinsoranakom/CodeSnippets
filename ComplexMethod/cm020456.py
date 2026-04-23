async def test_eiscp_discovery(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test successful eiscp discovery."""
    await setup_integration(hass, mock_config_entry)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "eiscp_discovery"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "eiscp_discovery"

    devices = result["data_schema"].schema["device"].container
    assert devices == {
        RECEIVER_INFO_2.identifier: _receiver_display_name(RECEIVER_INFO_2)
    }

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"device": RECEIVER_INFO_2.identifier}
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