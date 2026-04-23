async def test_form(
    hass: HomeAssistant,
    fakeimgbytes_png: bytes,
    hass_client: ClientSessionGenerator,
    user_flow: ConfigFlowResult,
    mock_create_stream: MagicMock,
    mock_setup_entry: AsyncMock,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test the form with a normal set of settings."""

    result1 = await hass.config_entries.flow.async_configure(
        user_flow["flow_id"],
        TESTDATA,
    )
    assert result1["type"] is FlowResultType.FORM
    assert result1["step_id"] == "user_confirm"

    # HA should now be serving a WS connection for a preview stream.
    ws_client = await hass_ws_client()
    flow_id = user_flow["flow_id"]
    await ws_client.send_json_auto_id(
        {
            "type": "generic_camera/start_preview",
            "flow_id": flow_id,
        },
    )
    json = await ws_client.receive_json()

    # Check stream_url is absolute (required by HLS player for child playlist URLs)
    stream_preview_url = json["event"]["attributes"]["stream_url"]
    assert stream_preview_url.startswith("http")

    client = await hass_client()
    still_preview_url = json["event"]["attributes"]["still_url"]
    # Check the preview image works.
    resp = await client.get(still_preview_url)
    assert resp.status == HTTPStatus.OK
    assert await resp.read() == fakeimgbytes_png

    result2 = await hass.config_entries.flow.async_configure(
        result1["flow_id"],
        user_input={CONF_CONFIRMED_OK: True},
    )
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "127_0_0_1"
    assert result2["options"] == {
        CONF_STILL_IMAGE_URL: "http://127.0.0.1/testurl/1",
        CONF_STREAM_SOURCE: "http://127.0.0.1/testurl/2",
        CONF_USERNAME: "fred_flintstone",
        CONF_PASSWORD: "bambam",
        CONF_CONTENT_TYPE: "image/png",
        SECTION_ADVANCED: {
            CONF_AUTHENTICATION: HTTP_BASIC_AUTHENTICATION,
            CONF_FRAMERATE: 5.0,
            CONF_VERIFY_SSL: False,
        },
    }

    # Check that the preview image is disabled after.
    resp = await client.get(still_preview_url)
    assert resp.status == HTTPStatus.NOT_FOUND