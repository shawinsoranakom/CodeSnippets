async def test_flow_same_device_multiple_sources(
    hass: HomeAssistant, manager: config_entries.ConfigEntries
) -> None:
    """Test discovery of the same devices from multiple discovery sources."""
    mock_integration(
        hass,
        MockModule("comp", async_setup_entry=AsyncMock(return_value=True)),
    )
    mock_platform(hass, "comp.config_flow", None)

    class TestFlow(config_entries.ConfigFlow):
        """Test flow."""

        VERSION = 1

        async def async_step_zeroconf(self, discovery_info=None):
            """Test zeroconf step."""
            return await self._async_discovery_handler(discovery_info)

        async def async_step_homekit(self, discovery_info=None):
            """Test homekit step."""
            return await self._async_discovery_handler(discovery_info)

        async def _async_discovery_handler(self, discovery_info=None):
            """Test any discovery handler."""
            await self.async_set_unique_id("thisid")
            self._abort_if_unique_id_configured()
            await asyncio.sleep(0.1)
            return await self.async_step_link()

        async def async_step_link(self, user_input=None):
            """Test a link step."""
            if user_input is None:
                return self.async_show_form(step_id="link")
            return self.async_create_entry(title="title", data={"token": "supersecret"})

    with mock_config_flow("comp", TestFlow):
        # Create one to be in progress
        flow1 = manager.flow.async_init(
            "comp", context={"source": config_entries.SOURCE_ZEROCONF}
        )
        flow2 = manager.flow.async_init(
            "comp", context={"source": config_entries.SOURCE_ZEROCONF}
        )
        flow3 = manager.flow.async_init(
            "comp", context={"source": config_entries.SOURCE_HOMEKIT}
        )
        _result1, result2, _result3 = await asyncio.gather(flow1, flow2, flow3)

        flows = hass.config_entries.flow.async_progress()
        assert len(flows) == 1
        assert flows[0]["context"]["unique_id"] == "thisid"

        # Finish flow
        result2 = await manager.flow.async_configure(
            flows[0]["flow_id"], user_input={"fake": "data"}
        )
        assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY

    assert len(hass.config_entries.flow.async_progress()) == 0

    entry = hass.config_entries.async_entries("comp")[0]
    assert entry.title == "title"
    assert entry.source in {
        config_entries.SOURCE_ZEROCONF,
        config_entries.SOURCE_HOMEKIT,
    }
    assert entry.unique_id == "thisid"