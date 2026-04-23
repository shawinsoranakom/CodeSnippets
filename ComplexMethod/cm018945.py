async def test_bad_credentials(hass: HomeAssistant) -> None:
    """Test when provided credentials are rejected."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    with (
        patch(
            "plexapi.myplex.MyPlexAccount", side_effect=plexapi.exceptions.Unauthorized
        ),
        patch("plexauth.PlexAuth.initiate_auth"),
        patch("plexauth.PlexAuth.token", return_value="BAD TOKEN"),
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
        assert result["errors"][CONF_TOKEN] == "faulty_credentials"