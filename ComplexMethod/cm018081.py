async def test_show_progress(hass: HomeAssistant, manager: MockFlowManager) -> None:
    """Test show progress logic."""
    manager.hass = hass
    events = []
    progress_update_events = async_capture_events(
        hass, data_entry_flow.EVENT_DATA_ENTRY_FLOW_PROGRESS_UPDATE
    )
    task_one_evt = asyncio.Event()
    task_two_evt = asyncio.Event()
    event_received_evt = asyncio.Event()

    @callback
    def capture_events(event: Event) -> None:
        events.append(event)
        event_received_evt.set()

    @manager.mock_reg_handler("test")
    class TestFlow(data_entry_flow.FlowHandler):
        VERSION = 5
        data = None
        start_task_two = False
        task_one: asyncio.Task[None] | None = None
        task_two: asyncio.Task[None] | None = None

        async def async_step_init(self, user_input=None):
            async def long_running_job_one() -> None:
                await task_one_evt.wait()

            async def long_running_job_two() -> None:
                self.async_update_progress(0.25)
                await task_two_evt.wait()
                self.async_update_progress(0.75)
                self.data = {"title": "Hello"}

            uncompleted_task: asyncio.Task[None] | None = None
            if not self.task_one:
                self.task_one = hass.async_create_task(long_running_job_one())

            progress_action = None
            if not self.task_one.done():
                progress_action = "task_one"
                uncompleted_task = self.task_one

            if not uncompleted_task:
                if not self.task_two:
                    self.task_two = hass.async_create_task(long_running_job_two())

                if not self.task_two.done():
                    progress_action = "task_two"
                    uncompleted_task = self.task_two

            if uncompleted_task:
                assert progress_action
                return self.async_show_progress(
                    progress_action=progress_action,
                    progress_task=uncompleted_task,
                )

            return self.async_show_progress_done(next_step_id="finish")

        async def async_step_finish(self, user_input=None):
            return self.async_create_entry(title=self.data["title"], data=self.data)

    hass.bus.async_listen(
        data_entry_flow.EVENT_DATA_ENTRY_FLOW_PROGRESSED,
        capture_events,
    )

    result = await manager.async_init("test")
    assert result["type"] == data_entry_flow.FlowResultType.SHOW_PROGRESS
    assert result["progress_action"] == "task_one"
    assert len(manager.async_progress()) == 1
    assert len(manager.async_progress_by_handler("test")) == 1
    assert manager.async_get(result["flow_id"])["handler"] == "test"

    # Set task one done and wait for event
    task_one_evt.set()
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
    assert result["type"] == data_entry_flow.FlowResultType.SHOW_PROGRESS
    assert result["progress_action"] == "task_two"
    assert len(progress_update_events) == 1
    assert progress_update_events[0].data == {
        "handler": "test",
        "flow_id": result["flow_id"],
        "progress": 0.25,
    }

    # Set task two done and wait for event
    task_two_evt.set()
    await event_received_evt.wait()
    event_received_evt.clear()
    assert len(events) == 2  # 1 for task one and 1 for task two
    assert events[1].data == {
        "handler": "test",
        "flow_id": result["flow_id"],
        "refresh": True,
    }
    assert len(progress_update_events) == 2
    assert progress_update_events[1].data == {
        "handler": "test",
        "flow_id": result["flow_id"],
        "progress": 0.75,
    }

    # Frontend refreshes the flow
    result = await manager.async_configure(result["flow_id"])
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "Hello"