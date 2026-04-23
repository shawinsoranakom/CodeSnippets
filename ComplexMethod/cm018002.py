async def test_create_entry_next_flow(
    hass: HomeAssistant, manager: config_entries.ConfigEntries
) -> None:
    """Test next_flow parameter for create entry."""

    async def mock_async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
        """Mock setup."""
        return True

    async_setup_entry = AsyncMock(return_value=True)
    mock_integration(
        hass,
        MockModule(
            "comp",
            async_setup=mock_async_setup,
            async_setup_entry=async_setup_entry,
        ),
    )
    mock_platform(hass, "comp.config_flow", None)

    class TestFlow(config_entries.ConfigFlow):
        """Test flow."""

        async def async_step_import(
            self, user_input: dict[str, Any] | None = None
        ) -> config_entries.ConfigFlowResult:
            """Test create entry with next_flow parameter."""
            result = await hass.config_entries.flow.async_init(
                "comp",
                context={"source": config_entries.SOURCE_USER},
            )
            return self.async_create_entry(
                title="import",
                data={"flow": "import"},
                next_flow=(config_entries.FlowType.CONFIG_FLOW, result["flow_id"]),
            )

        async def async_step_user(
            self, user_input: dict[str, Any] | None = None
        ) -> config_entries.ConfigFlowResult:
            """Test next step."""
            if user_input is None:
                return self.async_show_form(step_id="user")
            return self.async_create_entry(title="user", data={"flow": "user"})

    with mock_config_flow("comp", TestFlow):
        assert await async_setup_component(hass, "comp", {})

        result = await hass.config_entries.flow.async_init(
            "comp",
            context={"source": config_entries.SOURCE_IMPORT},
        )
        await hass.async_block_till_done()

        flows = hass.config_entries.flow.async_progress()
        assert len(flows) == 1
        user_flow = flows[0]
        assert async_setup_entry.call_count == 1

        entries = hass.config_entries.async_entries("comp")
        assert len(entries) == 1
        entry = entries[0]
        assert result == {
            "context": {"source": "import"},
            "data": {"flow": "import"},
            "description_placeholders": None,
            "description": None,
            "flow_id": ANY,
            "handler": "comp",
            "minor_version": 1,
            "next_flow": (config_entries.FlowType.CONFIG_FLOW, user_flow["flow_id"]),
            "options": {},
            "result": entry,
            "subentries": (),
            "title": "import",
            "type": FlowResultType.CREATE_ENTRY,
            "version": 1,
        }

        result = await hass.config_entries.flow.async_configure(
            user_flow["flow_id"], {}
        )
        await hass.async_block_till_done()

        assert async_setup_entry.call_count == 2
        entries = hass.config_entries.async_entries("comp")
        entry = next(entry for entry in entries if entry.data.get("flow") == "user")
        assert result == {
            "context": {"source": "user"},
            "data": {"flow": "user"},
            "description_placeholders": None,
            "description": None,
            "flow_id": user_flow["flow_id"],
            "handler": "comp",
            "minor_version": 1,
            "options": {},
            "result": entry,
            "subentries": (),
            "title": "user",
            "type": FlowResultType.CREATE_ENTRY,
            "version": 1,
        }