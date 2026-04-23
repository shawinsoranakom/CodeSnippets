async def test_external_step(hass: HomeAssistant, manager: MockFlowManager) -> None:
    """Test external step logic."""
    manager.hass = hass

    @manager.mock_reg_handler("test")
    class TestFlow(data_entry_flow.FlowHandler):
        VERSION = 5
        data = None

        async def async_step_init(self, user_input=None):
            if not user_input:
                return self.async_external_step(
                    step_id="init", url="https://example.com"
                )

            self.data = user_input
            return self.async_external_step_done(next_step_id="finish")

        async def async_step_finish(self, user_input=None):
            return self.async_create_entry(title=self.data["title"], data=self.data)

    events = async_capture_events(
        hass, data_entry_flow.EVENT_DATA_ENTRY_FLOW_PROGRESSED
    )

    result = await manager.async_init("test")
    assert result["type"] == data_entry_flow.FlowResultType.EXTERNAL_STEP
    assert len(manager.async_progress()) == 1
    assert len(manager.async_progress_by_handler("test")) == 1
    assert manager.async_get(result["flow_id"])["handler"] == "test"

    # Mimic external step
    # Called by integrations: `hass.config_entries.flow.async_configure(…)`
    result = await manager.async_configure(result["flow_id"], {"title": "Hello"})
    assert result["type"] == data_entry_flow.FlowResultType.EXTERNAL_STEP_DONE

    await hass.async_block_till_done()
    assert len(events) == 1
    assert events[0].data == {
        "handler": "test",
        "flow_id": result["flow_id"],
        "refresh": True,
    }

    # Frontend refreshes the flow
    result = await manager.async_configure(result["flow_id"])
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "Hello"