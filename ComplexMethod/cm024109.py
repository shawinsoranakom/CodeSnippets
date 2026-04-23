async def test_option_flow(
    hass: HomeAssistant, config_entry_setup: MockConfigEntry
) -> None:
    """Test config flow options."""
    assert CONF_STREAM_PROFILE not in config_entry_setup.options
    assert CONF_VIDEO_SOURCE not in config_entry_setup.options

    result = await hass.config_entries.options.async_init(config_entry_setup.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "configure_stream"
    assert set(result["data_schema"].schema[CONF_STREAM_PROFILE].container) == {
        DEFAULT_STREAM_PROFILE,
        "profile_1",
        "profile_2",
    }
    assert set(result["data_schema"].schema[CONF_VIDEO_SOURCE].container) == {
        DEFAULT_VIDEO_SOURCE,
        1,
    }

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_STREAM_PROFILE: "profile_1", CONF_VIDEO_SOURCE: 1},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_STREAM_PROFILE: "profile_1",
        CONF_VIDEO_SOURCE: 1,
    }
    assert config_entry_setup.options[CONF_STREAM_PROFILE] == "profile_1"
    assert config_entry_setup.options[CONF_VIDEO_SOURCE] == 1