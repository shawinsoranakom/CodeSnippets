async def test_on_create_entry_with_options_flow(
    hass: HomeAssistant, manager: config_entries.ConfigEntries
) -> None:
    """Test use async_on_create_entry with creating an options flow."""

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

        @staticmethod
        @callback
        def async_get_options_flow(config_entry: ConfigEntry) -> TestOptionsFlowHandler:
            """Get the options flow for this handler."""
            return TestOptionsFlowHandler()

        async def async_on_create_entry(
            self, result: config_entries.ConfigFlowResult
        ) -> config_entries.ConfigFlowResult:
            config_entry_id = result["result"].entry_id
            new_flow = await hass.config_entries.options.async_init(
                config_entry_id, context={"source": config_entries.SOURCE_USER}
            )
            result["next_flow"] = (
                config_entries.FlowType.OPTIONS_FLOW,
                new_flow["flow_id"],
            )
            return result

        async def async_step_user(
            self, user_input: dict[str, Any] | None = None
        ) -> config_entries.ConfigFlowResult:
            """Test next step."""
            if user_input is None:
                return self.async_show_form(step_id="user")
            return self.async_create_entry(
                title="user_flow",
                data={"flow": "user"},
            )

    class TestOptionsFlowHandler(config_entries.OptionsFlow):
        """Handle options."""

        async def async_step_init(
            self, user_input: dict[str, Any] | None = None
        ) -> config_entries.ConfigFlowResult:
            """Manage options."""

            if user_input is None:
                return self.async_show_form(step_id="init")
            return self.async_create_entry(title="options", data={"flow": "options"})

    with mock_config_flow("comp", TestFlow):
        assert await async_setup_component(hass, "comp", {})

        result = await hass.config_entries.flow.async_init(
            "comp", context={"source": config_entries.SOURCE_USER}
        )
        await hass.async_block_till_done()
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

        flows = hass.config_entries.flow.async_progress()
        assert len(flows) == 0
        option_flows = hass.config_entries.options.async_progress()
        assert len(option_flows) == 1
        option_flow = option_flows[0]

        entries = hass.config_entries.async_entries("comp")
        assert len(entries) == 1
        entry = entries[0]
        assert result == {
            "context": {"source": "user"},
            "data": {"flow": "user"},
            "description_placeholders": None,
            "description": None,
            "flow_id": ANY,
            "handler": "comp",
            "minor_version": 1,
            "next_flow": (
                config_entries.FlowType.OPTIONS_FLOW,
                option_flow["flow_id"],
            ),
            "options": {},
            "result": entry,
            "subentries": (),
            "title": "user_flow",
            "type": FlowResultType.CREATE_ENTRY,
            "version": 1,
        }

        result = await hass.config_entries.options.async_configure(
            option_flow["flow_id"], {}
        )
        option_flows = hass.config_entries.options.async_progress()
        assert len(option_flows) == 0

        assert result == {
            "context": {"source": "user"},
            "data": {"flow": "options"},
            "description_placeholders": None,
            "description": None,
            "flow_id": ANY,
            "handler": entry.entry_id,
            "title": "options",
            "type": FlowResultType.CREATE_ENTRY,
        }