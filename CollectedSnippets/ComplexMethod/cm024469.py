async def test_user_flow(hass: HomeAssistant) -> None:
    """Test the user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with (
        patch(
            "homeassistant.components.hive.config_flow.Auth.login",
            return_value={
                "ChallengeName": "SUCCESS",
                "AuthenticationResult": {
                    "RefreshToken": "mock-refresh-token",
                    "AccessToken": "mock-access-token",
                },
            },
        ),
        patch(
            "homeassistant.components.hive.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == USERNAME
    assert result2["data"] == {
        CONF_USERNAME: USERNAME,
        CONF_PASSWORD: PASSWORD,
        "tokens": {
            "AuthenticationResult": {
                "AccessToken": "mock-access-token",
                "RefreshToken": "mock-refresh-token",
            },
            "ChallengeName": "SUCCESS",
        },
    }

    assert len(mock_setup_entry.mock_calls) == 1
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1