async def test_implementation(
    hass: HomeAssistant,
    flow_handler: type[config_entry_oauth2_flow.AbstractOAuth2FlowHandler],
) -> None:
    """Test Cloud OAuth2 implementation."""
    hass.data[DATA_CLOUD] = None

    impl = account_link.CloudOAuth2Implementation(hass, "test")
    assert impl.name == "Home Assistant Cloud"
    assert impl.domain == "cloud"

    flow_handler.async_register_implementation(hass, impl)

    flow_finished = asyncio.Future()

    helper = Mock(
        async_get_authorize_url=AsyncMock(return_value="http://example.com/auth"),
        async_get_tokens=Mock(return_value=flow_finished),
    )

    with patch(
        "hass_nabucasa.account_link.AuthorizeAccountHelper", return_value=helper
    ):
        result = await hass.config_entries.flow.async_init(
            TEST_DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    assert result["type"] is FlowResultType.EXTERNAL_STEP
    assert result["url"] == "http://example.com/auth"

    flow_finished.set_result(
        {
            "refresh_token": "mock-refresh",
            "access_token": "mock-access",
            "expires_in": 10,
            "token_type": "bearer",
        }
    )
    await hass.async_block_till_done()

    # Flow finished!
    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert result["data"]["auth_implementation"] == "cloud"

    expires_at = result["data"]["token"].pop("expires_at")
    assert round(expires_at - time()) == 10

    assert result["data"]["token"] == {
        "refresh_token": "mock-refresh",
        "access_token": "mock-access",
        "token_type": "bearer",
        "expires_in": 10,
    }

    entry = hass.config_entries.async_entries(TEST_DOMAIN)[0]

    assert (
        await config_entry_oauth2_flow.async_get_config_entry_implementation(
            hass, entry
        )
        is impl
    )