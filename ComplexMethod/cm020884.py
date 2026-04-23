async def test_options_template_error(
    hass: HomeAssistant,
    mock_create_stream: MagicMock,
    config_entry: MockConfigEntry,
) -> None:
    """Test the options flow with a template error."""
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    # try updating the still image url
    data = TESTDATA.copy()
    data[CONF_STILL_IMAGE_URL] = "http://127.0.0.1/testurl/2"
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input=data,
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "user_confirm"

    result2a = await hass.config_entries.options.async_configure(
        result2["flow_id"], user_input={CONF_CONFIRMED_OK: True}
    )
    assert result2a["type"] is FlowResultType.CREATE_ENTRY

    result3 = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result3["type"] is FlowResultType.FORM
    assert result3["step_id"] == "init"

    # verify that an invalid template reports the correct UI error.
    data[CONF_STILL_IMAGE_URL] = "http://127.0.0.1/testurl/{{1/0}}"
    result4 = await hass.config_entries.options.async_configure(
        result3["flow_id"],
        user_input=data,
    )
    assert result4.get("type") is FlowResultType.FORM
    assert result4["errors"] == {"still_image_url": "template_error"}

    # verify that an invalid template reports the correct UI error.
    data[CONF_STILL_IMAGE_URL] = "http://127.0.0.1/testurl/1"
    data[CONF_STREAM_SOURCE] = "http://127.0.0.2/testurl/{{1/0}}"
    result5 = await hass.config_entries.options.async_configure(
        result4["flow_id"],
        user_input=data,
    )

    assert result5.get("type") is FlowResultType.FORM
    assert result5["errors"] == {"stream_source": "template_error"}

    # verify that an relative stream url is rejected.
    data[CONF_STILL_IMAGE_URL] = "http://127.0.0.1/testurl/1"
    data[CONF_STREAM_SOURCE] = "relative/stream.mjpeg"
    result6 = await hass.config_entries.options.async_configure(
        result5["flow_id"],
        user_input=data,
    )
    assert result6.get("type") is FlowResultType.FORM
    assert result6["errors"] == {"stream_source": "relative_url"}

    # verify that an malformed stream url is rejected.
    data[CONF_STILL_IMAGE_URL] = "http://127.0.0.1/testurl/1"
    data[CONF_STREAM_SOURCE] = "http://example.com:45:56"
    result7 = await hass.config_entries.options.async_configure(
        result6["flow_id"],
        user_input=data,
    )
    assert result7.get("type") is FlowResultType.FORM
    assert result7["errors"] == {"stream_source": "malformed_url"}