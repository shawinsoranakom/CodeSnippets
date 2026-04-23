async def test_async_has_matching_discovery_flow(
    hass: HomeAssistant, manager: config_entries.ConfigEntries
) -> None:
    """Test we can check for matching discovery flows."""
    assert (
        manager.flow.async_has_matching_discovery_flow(
            "test",
            {"source": config_entries.SOURCE_HOMEKIT},
            {"properties": {"id": "aa:bb:cc:dd:ee:ff"}},
        )
        is False
    )

    mock_integration(hass, MockModule("test"))
    mock_platform(hass, "test.config_flow", None)

    class TestFlow(config_entries.ConfigFlow):
        VERSION = 5

        async def async_step_init(self, user_input=None):
            return self.async_show_progress(
                step_id="init",
                progress_action="task_one",
            )

        async def async_step_homekit(self, discovery_info=None):
            return await self.async_step_init(discovery_info)

    with mock_config_flow("test", TestFlow):
        result = await manager.flow.async_init(
            "test",
            context={"source": config_entries.SOURCE_HOMEKIT},
            data={"properties": {"id": "aa:bb:cc:dd:ee:ff"}},
        )
    assert result["type"] == data_entry_flow.FlowResultType.SHOW_PROGRESS
    assert result["progress_action"] == "task_one"
    assert len(manager.flow.async_progress()) == 1
    assert len(manager.flow.async_progress_by_handler("test")) == 1
    assert (
        len(
            manager.flow.async_progress_by_handler(
                "test", match_context={"source": config_entries.SOURCE_HOMEKIT}
            )
        )
        == 1
    )
    assert (
        len(
            manager.flow.async_progress_by_handler(
                "test", match_context={"source": config_entries.SOURCE_BLUETOOTH}
            )
        )
        == 0
    )
    assert manager.flow.async_get(result["flow_id"])["handler"] == "test"

    assert (
        manager.flow.async_has_matching_discovery_flow(
            "test",
            {"source": config_entries.SOURCE_HOMEKIT},
            {"properties": {"id": "aa:bb:cc:dd:ee:ff"}},
        )
        is True
    )
    assert (
        manager.flow.async_has_matching_discovery_flow(
            "test",
            {"source": config_entries.SOURCE_SSDP},
            {"properties": {"id": "aa:bb:cc:dd:ee:ff"}},
        )
        is False
    )
    assert (
        manager.flow.async_has_matching_discovery_flow(
            "other",
            {"source": config_entries.SOURCE_HOMEKIT},
            {"properties": {"id": "aa:bb:cc:dd:ee:ff"}},
        )
        is False
    )