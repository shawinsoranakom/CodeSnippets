async def test_ignore_flow(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    flow_context: dict,
    entry_discovery_keys: dict[str, tuple[DiscoveryKey, ...]],
) -> None:
    """Test we can ignore a flow."""
    assert await async_setup_component(hass, "config", {})
    mock_integration(
        hass, MockModule("test", async_setup_entry=AsyncMock(return_value=True))
    )
    mock_platform(hass, "test.config_flow", None)

    class TestFlow(core_ce.ConfigFlow):
        VERSION = 1

        async def async_step_user(self, user_input=None):
            await self.async_set_unique_id("mock-unique-id")
            return self.async_show_form(step_id="account")

        async def async_step_account(self, user_input=None):
            raise NotImplementedError

    ws_client = await hass_ws_client(hass)

    with mock_config_flow("test", TestFlow):
        result = await hass.config_entries.flow.async_init(
            "test", context={"source": core_ce.SOURCE_USER} | flow_context
        )
        assert result["type"] is FlowResultType.FORM

        await ws_client.send_json(
            {
                "id": 5,
                "type": "config_entries/ignore_flow",
                "flow_id": result["flow_id"],
                "title": "Test Integration",
            }
        )
        response = await ws_client.receive_json()

        assert response["success"]

    assert len(hass.config_entries.flow.async_progress()) == 0

    entry = hass.config_entries.async_entries("test")[0]
    assert entry.source == "ignore"
    assert entry.unique_id == "mock-unique-id"
    assert entry.title == "Test Integration"
    assert entry.data == {}
    assert entry.discovery_keys == entry_discovery_keys