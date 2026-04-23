async def test_flow_without_subscriptions(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
) -> None:
    """Check flow continues even without subscriptions since user has their own channel."""
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

    service = MockYouTube(hass, subscriptions_fixture="get_no_subscriptions.json")
    with (
        patch("homeassistant.components.youtube.async_setup_entry", return_value=True),
        patch(
            "homeassistant.components.youtube.config_flow.YouTube", return_value=service
        ),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "channels"

        # Verify the form schema contains only the user's own channel
        schema = result["data_schema"]
        channels = schema.schema[CONF_CHANNELS].config["options"]
        assert len(channels) == 1
        assert channels[0]["value"] == "UC_x5XG1OV2P6uZZ5FSM9Ttw"
        assert "(Your Channel)" in channels[0]["label"]

        # Test selecting the own channel
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_CHANNELS: ["UC_x5XG1OV2P6uZZ5FSM9Ttw"]},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TITLE
    assert "result" in result
    assert result["result"].unique_id == "UC_x5XG1OV2P6uZZ5FSM9Ttw"
    assert "token" in result["result"].data
    assert result["result"].data["token"]["access_token"] == "mock-access-token"
    assert result["result"].data["token"]["refresh_token"] == "mock-refresh-token"
    assert result["options"] == {CONF_CHANNELS: ["UC_x5XG1OV2P6uZZ5FSM9Ttw"]}