async def test_options_use_wallclock_as_timestamps(
    hass: HomeAssistant,
    mock_create_stream: MagicMock,
    hass_client: ClientSessionGenerator,
    hass_ws_client: WebSocketGenerator,
    fakeimgbytes_png: bytes,
    config_entry: MockConfigEntry,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test the use_wallclock_as_timestamps option flow."""

    result = await hass.config_entries.options.async_init(
        config_entry.entry_id, context={"show_advanced_options": True}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    data = deepcopy(TESTDATA)
    data[SECTION_ADVANCED][CONF_USE_WALLCLOCK_AS_TIMESTAMPS] = True
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input=data,
    )
    assert result2["type"] is FlowResultType.FORM

    ws_client = await hass_ws_client()
    flow_id = result2["flow_id"]
    await ws_client.send_json_auto_id(
        {
            "type": "generic_camera/start_preview",
            "flow_id": flow_id,
            "flow_type": "options_flow",
        },
    )
    json = await ws_client.receive_json()

    client = await hass_client()
    still_preview_url = json["event"]["attributes"]["still_url"]
    # Check the preview image works.
    resp = await client.get(still_preview_url)
    assert resp.status == HTTPStatus.OK
    assert await resp.read() == fakeimgbytes_png

    # Test what happens if user rejects the preview
    result3 = await hass.config_entries.options.async_configure(
        result2["flow_id"], user_input={CONF_CONFIRMED_OK: False}
    )
    assert result3["type"] is FlowResultType.FORM
    assert result3["step_id"] == "init"
    result4 = await hass.config_entries.options.async_configure(
        result3["flow_id"],
        user_input=data,
    )
    assert result4["type"] is FlowResultType.FORM
    assert result4["step_id"] == "user_confirm"
    result5 = await hass.config_entries.options.async_configure(
        result4["flow_id"],
        user_input={CONF_CONFIRMED_OK: True},
    )
    assert result5["type"] is FlowResultType.CREATE_ENTRY