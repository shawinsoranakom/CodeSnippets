async def test_zeroconf_flow(hass: HomeAssistant) -> None:
    """Test zeroconf config flow."""
    discovery_info = dataclasses.replace(MOCK_ZEROCONF_SERVICE_INFO)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=discovery_info
    )

    # Form should always show even if all required properties are discovered
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # Apply discovery updates to entry to mimic when user hits submit without changing
    # defaults which were set from discovery parameters
    user_input = result["data_schema"](
        {
            CONF_HOST: f"{discovery_info.host}:{discovery_info.port}",
            CONF_NAME: discovery_info.name[: -(len(discovery_info.type) + 1)],
            CONF_DEVICE_CLASS: "speaker",
        }
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=user_input
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == NAME
    assert result["data"][CONF_HOST] == HOST
    assert result["data"][CONF_NAME] == NAME
    assert result["data"][CONF_DEVICE_CLASS] == MediaPlayerDeviceClass.SPEAKER