async def test_show_progress_error(
    hass: HomeAssistant, manager: MockFlowManager
) -> None:
    """Test show progress logic."""
    manager.hass = hass
    events = []
    event_received_evt = asyncio.Event()

    @callback
    def capture_events(event: Event) -> None:
        events.append(event)
        event_received_evt.set()

    @manager.mock_reg_handler("test")
    class TestFlow(data_entry_flow.FlowHandler):
        VERSION = 5
        data = None
        progress_task: asyncio.Task[None] | None = None

        async def async_step_init(self, user_input=None):
            async def long_running_task() -> None:
                await asyncio.sleep(0)
                raise TypeError

            if not self.progress_task:
                self.progress_task = hass.async_create_task(long_running_task())
            if self.progress_task and self.progress_task.done():
                if self.progress_task.exception():
                    return self.async_show_progress_done(next_step_id="error")
                return self.async_show_progress_done(next_step_id="no_error")
            return self.async_show_progress(
                progress_action="task", progress_task=self.progress_task
            )

        async def async_step_error(self, user_input=None):
            return self.async_abort(reason="error")

    hass.bus.async_listen(
        data_entry_flow.EVENT_DATA_ENTRY_FLOW_PROGRESSED,
        capture_events,
    )

    result = await manager.async_init("test")
    assert result["type"] == data_entry_flow.FlowResultType.SHOW_PROGRESS
    assert result["progress_action"] == "task"
    assert len(manager.async_progress()) == 1
    assert len(manager.async_progress_by_handler("test")) == 1
    assert manager.async_get(result["flow_id"])["handler"] == "test"

    # Set task one done and wait for event
    await event_received_evt.wait()
    event_received_evt.clear()
    assert len(events) == 1
    assert events[0].data == {
        "handler": "test",
        "flow_id": result["flow_id"],
        "refresh": True,
    }

    # Frontend refreshes the flow
    result = await manager.async_configure(result["flow_id"])
    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "error"