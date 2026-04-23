async def test_get_progress_subscribe(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test querying for the flows that are in progress."""
    assert await async_setup_component(hass, "config", {})
    mock_platform(hass, "test.config_flow", None)
    ws_client = await hass_ws_client(hass)

    mock_integration(
        hass, MockModule("test", async_setup_entry=AsyncMock(return_value=True))
    )

    entry = MockConfigEntry(domain="test", title="Test", entry_id="1234")
    entry.add_to_hass(hass)

    class TestFlow(core_ce.ConfigFlow):
        VERSION = 5

        async def async_step_bluetooth(
            self, discovery_info: HassioServiceInfo
        ) -> ConfigFlowResult:
            """Handle a bluetooth discovery."""
            return self.async_abort(reason="already_configured")

        async def async_step_hassio(
            self, discovery_info: HassioServiceInfo
        ) -> ConfigFlowResult:
            """Handle a Hass.io discovery."""
            return await self.async_step_account()

        async def async_step_account(self, user_input: dict[str, Any] | None = None):
            """Show a form to the user."""
            return self.async_show_form(step_id="account")

        async def async_step_user(self, user_input: dict[str, Any] | None = None):
            """Handle a config flow initialized by the user."""
            return await self.async_step_account()

        async def async_step_reauth(self, user_input: dict[str, Any] | None = None):
            """Handle a reauthentication flow."""
            nonlocal entry
            assert self._get_reauth_entry() is entry
            return await self.async_step_account()

        async def async_step_reconfigure(
            self, user_input: dict[str, Any] | None = None
        ):
            """Handle a reconfiguration flow initialized by the user."""
            nonlocal entry
            assert self._get_reconfigure_entry() is entry
            return await self.async_step_account()

    await ws_client.send_json({"id": 1, "type": "config_entries/flow/subscribe"})
    response = await ws_client.receive_json()
    assert response == {"id": 1, "event": [], "type": "event"}
    response = await ws_client.receive_json()
    assert response == {"id": 1, "result": None, "success": True, "type": "result"}

    flow_context = {
        "bluetooth": {"source": core_ce.SOURCE_BLUETOOTH},
        "hassio": {"source": core_ce.SOURCE_HASSIO},
        "user": {"source": core_ce.SOURCE_USER},
        "reauth": {"source": core_ce.SOURCE_REAUTH, "entry_id": "1234"},
        "reconfigure": {"source": core_ce.SOURCE_RECONFIGURE, "entry_id": "1234"},
    }
    forms = {}

    with mock_config_flow("test", TestFlow):
        for key, context in flow_context.items():
            forms[key] = await hass.config_entries.flow.async_init(
                "test", context=context
            )

    assert forms["bluetooth"]["type"] == data_entry_flow.FlowResultType.ABORT
    for key in ("hassio", "user", "reauth", "reconfigure"):
        assert forms[key]["type"] == data_entry_flow.FlowResultType.FORM
        assert forms[key]["step_id"] == "account"

    for key in ("hassio", "user", "reauth", "reconfigure"):
        hass.config_entries.flow.async_abort(forms[key]["flow_id"])

    # Uninitialized flows and flows with SOURCE_USER and SOURCE_RECONFIGURE
    # should be filtered out
    for key in ("hassio", "reauth"):
        response = await ws_client.receive_json()
        assert response == {
            "event": [
                {
                    "flow": {
                        "flow_id": forms[key]["flow_id"],
                        "handler": "test",
                        "step_id": "account",
                        "context": flow_context[key],
                    },
                    "flow_id": forms[key]["flow_id"],
                    "type": "added",
                }
            ],
            "id": 1,
            "type": "event",
        }
    for key in ("hassio", "reauth"):
        response = await ws_client.receive_json()
        assert response == {
            "event": [
                {
                    "flow_id": forms[key]["flow_id"],
                    "type": "removed",
                }
            ],
            "id": 1,
            "type": "event",
        }