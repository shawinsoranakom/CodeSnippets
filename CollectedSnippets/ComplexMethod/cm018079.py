async def test_finish_callback_change_result_type(hass: HomeAssistant) -> None:
    """Test finish callback can change result type."""

    class TestFlow(data_entry_flow.FlowHandler):
        VERSION = 1

        async def async_step_init(self, input):
            """Return init form with one input field 'count'."""
            if input is not None:
                return self.async_create_entry(title="init", data=input)
            return self.async_show_form(
                step_id="init", data_schema=vol.Schema({"count": int})
            )

    class FlowManager(data_entry_flow.FlowManager):
        async def async_create_flow(self, handler_key, *, context, data):
            """Create a test flow."""
            return TestFlow()

        async def async_finish_flow(self, flow, result):
            """Redirect to init form if count <= 1."""
            if result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY:
                if result["data"] is None or result["data"].get("count", 0) <= 1:
                    return flow.async_show_form(
                        step_id="init", data_schema=vol.Schema({"count": int})
                    )
                result["result"] = result["data"]["count"]
            return result

    manager = FlowManager(hass)

    result = await manager.async_init("test")
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await manager.async_configure(result["flow_id"], {"count": 0})
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "init"
    assert "result" not in result

    result = await manager.async_configure(result["flow_id"], {"count": 2})
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["result"] == 2