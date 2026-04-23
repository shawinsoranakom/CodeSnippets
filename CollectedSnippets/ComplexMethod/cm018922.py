async def test_hassio_flow(hass: HomeAssistant) -> None:
    """Test HassIO discovery flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_HASSIO},
        data=_HASSIO_DISCOVERY,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "discovery_confirm"
    assert not result["errors"]

    # Cannot connect to server => retry
    with patch(
        "homeassistant.components.onewire.onewirehub.OWServerStatelessProxy.validate",
        side_effect=OWServerConnectionError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "discovery_confirm"
    assert result["errors"] == {"base": "cannot_connect"}

    # Connect OK
    with patch(
        "homeassistant.components.onewire.onewirehub.OWServerStatelessProxy.validate",
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    new_entry = result["result"]
    assert new_entry.title == "owserver (1-wire)"
    assert new_entry.data == {CONF_HOST: "1302b8e0-owserver", CONF_PORT: 4304}