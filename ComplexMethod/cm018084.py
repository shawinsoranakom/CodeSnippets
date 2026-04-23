async def test_show_progress_legacy(
    hass: HomeAssistant, manager: MockFlowManager, caplog: pytest.LogCaptureFixture
) -> None:
    """Test show progress logic.

    This tests the deprecated version where the config flow is responsible for
    resuming the flow.
    """
    manager.hass = hass

    @manager.mock_reg_handler("test")
    class TestFlow(data_entry_flow.FlowHandler):
        VERSION = 5
        data = None
        task_one_done = False
        task_two_done = False

        async def async_step_init(self, user_input=None):
            if user_input and "task_finished" in user_input:
                if user_input["task_finished"] == 1:
                    self.task_one_done = True
                elif user_input["task_finished"] == 2:
                    self.task_two_done = True

            if not self.task_one_done:
                progress_action = "task_one"
            elif not self.task_two_done:
                progress_action = "task_two"
            if not self.task_one_done or not self.task_two_done:
                return self.async_show_progress(
                    step_id="init",
                    progress_action=progress_action,
                )

            self.data = user_input
            return self.async_show_progress_done(next_step_id="finish")

        async def async_step_finish(self, user_input=None):
            return self.async_create_entry(title=self.data["title"], data=self.data)

    events = async_capture_events(
        hass, data_entry_flow.EVENT_DATA_ENTRY_FLOW_PROGRESSED
    )

    result = await manager.async_init("test")
    assert result["type"] == data_entry_flow.FlowResultType.SHOW_PROGRESS
    assert result["progress_action"] == "task_one"
    assert len(manager.async_progress()) == 1
    assert len(manager.async_progress_by_handler("test")) == 1
    assert manager.async_get(result["flow_id"])["handler"] == "test"

    # Mimic task one done and moving to task two
    # Called by integrations: `hass.config_entries.flow.async_configure(…)`
    result = await manager.async_configure(result["flow_id"], {"task_finished": 1})
    assert result["type"] == data_entry_flow.FlowResultType.SHOW_PROGRESS
    assert result["progress_action"] == "task_two"

    await hass.async_block_till_done()
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

    # Mimic task two done and continuing step
    # Called by integrations: `hass.config_entries.flow.async_configure(…)`
    result = await manager.async_configure(
        result["flow_id"], {"task_finished": 2, "title": "Hello"}
    )
    # Note: The SHOW_PROGRESS_DONE is not hidden from frontend when flows manage
    # the progress tasks themselves
    assert result["type"] == data_entry_flow.FlowResultType.SHOW_PROGRESS_DONE

    # Frontend refreshes the flow
    result = await manager.async_configure(
        result["flow_id"], {"task_finished": 2, "title": "Hello"}
    )
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "Hello"

    await hass.async_block_till_done()
    assert len(events) == 2  # 1 for task one and 1 for task two
    assert events[1].data == {
        "handler": "test",
        "flow_id": result["flow_id"],
        "refresh": True,
    }

    # Check for deprecation warning
    assert (
        "tests.test_data_entry_flow::TestFlow calls async_show_progress without passing"
        " a progress task, this is not valid and will break in Home Assistant "
        "Core 2024.8."
    ) in caplog.text