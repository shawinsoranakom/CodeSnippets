async def test_flow_successful(hass: HomeAssistant) -> None:
    """Test with required fields only."""
    with (
        patch("aiosyncthing.system.System.status", return_value={"myID": "server-id"}),
        patch(
            "homeassistant.components.syncthing.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "user"},
            data={
                CONF_NAME: NAME,
                CONF_URL: URL,
                CONF_TOKEN: TOKEN,
                CONF_VERIFY_SSL: VERIFY_SSL,
            },
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == "http://127.0.0.1:8384"
        assert result["data"][CONF_NAME] == NAME
        assert result["data"][CONF_URL] == URL
        assert result["data"][CONF_TOKEN] == TOKEN
        assert result["data"][CONF_VERIFY_SSL] == VERIFY_SSL
        assert len(mock_setup_entry.mock_calls) == 1