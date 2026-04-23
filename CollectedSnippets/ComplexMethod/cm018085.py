async def test_show_menu(
    hass: HomeAssistant,
    manager: MockFlowManager,
    menu_options: list[str] | dict[str, str],
    sort: bool | None,
    expect_sort: bool | None,
) -> None:
    """Test show menu."""
    manager.hass = hass

    @manager.mock_reg_handler("test")
    class TestFlow(data_entry_flow.FlowHandler):
        VERSION = 5
        data = None
        task_one_done = False

        async def async_step_init(self, user_input=None):
            return self.async_show_menu(
                step_id="init",
                menu_options=menu_options,
                description_placeholders={"name": "Paulus"},
                sort=sort,
            )

        async def async_step_target1(self, user_input=None):
            return self.async_show_form(step_id="target1")

        async def async_step_target2(self, user_input=None):
            return self.async_show_form(step_id="target2")

    result = await manager.async_init("test")
    assert result["type"] == data_entry_flow.FlowResultType.MENU
    assert result["menu_options"] == menu_options
    assert result["description_placeholders"] == {"name": "Paulus"}
    assert result.get("sort") == expect_sort
    assert len(manager.async_progress()) == 1
    assert len(manager.async_progress_by_handler("test")) == 1
    assert manager.async_get(result["flow_id"])["handler"] == "test"

    # Mimic picking a step
    result = await manager.async_configure(
        result["flow_id"], {"next_step_id": "target1"}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "target1"