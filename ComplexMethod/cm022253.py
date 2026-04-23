async def test_own_channel_included(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
) -> None:
    """Test that the user's own channel is included in the list of selectable channels."""
    result = await hass.config_entries.flow.async_init(
        "youtube", context={"source": config_entries.SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    assert result["url"] == (
        f"{GOOGLE_AUTH_URI}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}&scope={'+'.join(SCOPES)}"
        "&access_type=offline&prompt=consent"
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200
    assert resp.headers["content-type"] == "text/html; charset=utf-8"

    with (
        patch(
            "homeassistant.components.youtube.async_setup_entry", return_value=True
        ) as mock_setup,
        patch(
            "homeassistant.components.youtube.config_flow.YouTube",
            return_value=MockYouTube(hass),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "channels"

        # Verify the form schema contains the user's own channel
        schema = result["data_schema"]
        channels = schema.schema[CONF_CHANNELS].config["options"]
        assert any(
            channel["value"] == "UC_x5XG1OV2P6uZZ5FSM9Ttw"
            and "(Your Channel)" in channel["label"]
            for channel in channels
        )

        # Test selecting both own channel and a subscribed channel
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_CHANNELS: ["UC_x5XG1OV2P6uZZ5FSM9Ttw", "UC_x5XG1OV2P6uZZ5FSM9Ttw"]
            },
        )

    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    assert len(mock_setup.mock_calls) == 1

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TITLE
    assert "result" in result
    assert result["result"].unique_id == "UC_x5XG1OV2P6uZZ5FSM9Ttw"
    assert "token" in result["result"].data
    assert result["result"].data["token"]["access_token"] == "mock-access-token"
    assert result["result"].data["token"]["refresh_token"] == "mock-refresh-token"
    assert result["options"] == {
        CONF_CHANNELS: ["UC_x5XG1OV2P6uZZ5FSM9Ttw", "UC_x5XG1OV2P6uZZ5FSM9Ttw"]
    }