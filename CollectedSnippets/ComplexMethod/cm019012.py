async def test_constructor_loads_info_from_config(hass: HomeAssistant) -> None:
    """Test non-dev mode loads info from SERVERS constant."""
    with patch("hass_nabucasa.Cloud.initialize"):
        result = await async_setup_component(
            hass,
            "cloud",
            {
                "http": {},
                "cloud": {
                    CONF_MODE: MODE_DEV,
                    "cognito_client_id": "test-cognito_client_id",
                    "user_pool_id": "test-user_pool_id",
                    "region": "test-region",
                    "api_server": "test-api-server",
                    "relayer_server": "test-relayer-server",
                    "acme_server": "test-acme-server",
                    "remotestate_server": "test-remotestate-server",
                    "discovery_service_actions": {
                        "lorem_ipsum": "https://lorem.ipsum/test-url"
                    },
                },
            },
        )
        assert result

    cl = hass.data[DATA_CLOUD]
    assert cl.mode == MODE_DEV
    assert cl.cognito_client_id == "test-cognito_client_id"
    assert cl.user_pool_id == "test-user_pool_id"
    assert cl.region == "test-region"
    assert cl.relayer_server == "test-relayer-server"
    assert cl.iot.ws_server_url == "wss://test-relayer-server/websocket"
    assert cl.acme_server == "test-acme-server"
    assert cl.api_server == "test-api-server"
    assert cl.remotestate_server == "test-remotestate-server"
    assert (
        cl.service_discovery._action_overrides["lorem_ipsum"]
        == "https://lorem.ipsum/test-url"
    )