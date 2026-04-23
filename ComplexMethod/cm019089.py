async def test_integration_log_info_discovered_flows(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, hass_admin_user: MockUser
) -> None:
    """Test that log info includes discovered flows."""
    assert await async_setup_component(hass, "logger", {})

    # Set up a discovery flow (zeroconf)
    mock_integration(hass, MockModule("discovered_integration"))
    mock_platform(hass, "discovered_integration.config_flow", None)

    class DiscoveryFlow(config_entries.ConfigFlow, domain="discovered_integration"):
        """Test discovery flow."""

        VERSION = 1

        async def async_step_zeroconf(self, discovery_info=None):
            """Test zeroconf step."""
            return self.async_show_form(step_id="zeroconf")

    # Set up a user flow (non-discovery)
    mock_integration(hass, MockModule("user_flow_integration"))
    mock_platform(hass, "user_flow_integration.config_flow", None)

    class UserFlow(config_entries.ConfigFlow, domain="user_flow_integration"):
        """Test user flow."""

        VERSION = 1

        async def async_step_user(self, user_input=None):
            """Test user step."""
            return self.async_show_form(step_id="user")

    with (
        mock_config_flow("discovered_integration", DiscoveryFlow),
        mock_config_flow("user_flow_integration", UserFlow),
    ):
        # Start both flows
        await hass.config_entries.flow.async_init(
            "discovered_integration",
            context={"source": config_entries.SOURCE_ZEROCONF},
        )
        await hass.config_entries.flow.async_init(
            "user_flow_integration",
            context={"source": config_entries.SOURCE_USER},
        )

        # Verify both flows are in progress
        flows = hass.config_entries.flow.async_progress()
        assert len(flows) == 2

        websocket_client = await hass_ws_client()
        await websocket_client.send_json({"id": 7, "type": "logger/log_info"})

        msg = await websocket_client.receive_json()
        assert msg["id"] == 7
        assert msg["type"] == TYPE_RESULT
        assert msg["success"]

        domains = [item["domain"] for item in msg["result"]]
        # Discovery flow should be included
        assert "discovered_integration" in domains
        # User flow should NOT be included (not a discovery source)
        assert "user_flow_integration" not in domains