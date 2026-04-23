async def test_show_progress_hidden_from_frontend(
    hass: HomeAssistant, manager: MockFlowManager
) -> None:
    """Test show progress done is not sent to frontend."""
    manager.hass = hass
    async_show_progress_done_called = False
    progress_task: asyncio.Task[None] | None = None

    @manager.mock_reg_handler("test")
    class TestFlow(data_entry_flow.FlowHandler):
        VERSION = 5
        data = None

        async def async_step_init(self, user_input=None):
            nonlocal progress_task

            async def long_running_job() -> None:
                await asyncio.sleep(0)

            if not progress_task:
                progress_task = hass.async_create_task(long_running_job())
            if progress_task.done():
                nonlocal async_show_progress_done_called
                async_show_progress_done_called = True
                return self.async_show_progress_done(next_step_id="finish")
            return self.async_show_progress(
                step_id="init",
                progress_action="task",
                # Set to a task which never finishes to simulate flow manager has not
                # yet called when frontend loads
                progress_task=hass.async_create_task(asyncio.Event().wait()),
            )

        async def async_step_finish(self, user_input=None):
            return self.async_create_entry(title=None, data=self.data)

    result = await manager.async_init("test")
    assert result["type"] == data_entry_flow.FlowResultType.SHOW_PROGRESS
    assert result["progress_action"] == "task"
    assert len(manager.async_progress()) == 1
    assert len(manager.async_progress_by_handler("test")) == 1
    assert manager.async_get(result["flow_id"])["handler"] == "test"

    await progress_task
    assert not async_show_progress_done_called

    # Frontend refreshes the flow
    result = await manager.async_configure(result["flow_id"])
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert async_show_progress_done_called