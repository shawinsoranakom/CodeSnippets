async def test_no_servers_found(
    hass: HomeAssistant,
    mock_plex_calls,
    requests_mock: requests_mock.Mocker,
    empty_payload,
) -> None:
    """Test when no servers are on an account."""
    requests_mock.get("https://plex.tv/api/v2/resources", text=empty_payload)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    with (
        patch("plexauth.PlexAuth.initiate_auth"),
        patch("plexauth.PlexAuth.token", return_value=MOCK_TOKEN),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
        assert result["type"] is FlowResultType.EXTERNAL_STEP

        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        assert result["type"] is FlowResultType.EXTERNAL_STEP_DONE

        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"]["base"] == "no_servers"