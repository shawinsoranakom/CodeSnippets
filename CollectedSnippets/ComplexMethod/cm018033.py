async def test_options_flow_config_entry(
    hass: HomeAssistant, manager: config_entries.ConfigEntries
) -> None:
    """Test _config_entry_id and config_entry properties in options flow."""
    original_entry = MockConfigEntry(domain="test", data={})
    original_entry.add_to_hass(hass)

    mock_setup_entry = AsyncMock(return_value=True)

    mock_integration(hass, MockModule("test", async_setup_entry=mock_setup_entry))
    mock_platform(hass, "test.config_flow", None)

    class TestFlow(config_entries.ConfigFlow):
        """Test flow."""

        @staticmethod
        @callback
        def async_get_options_flow(config_entry):
            """Test options flow."""

            class _OptionsFlow(config_entries.OptionsFlow):
                """Test flow."""

                def __init__(self) -> None:
                    """Test initialisation."""
                    try:
                        self.init_entry_id = self._config_entry_id
                    except ValueError as err:
                        self.init_entry_id = err
                    try:
                        self.init_entry = self.config_entry
                    except ValueError as err:
                        self.init_entry = err

                async def async_step_init(self, user_input=None):
                    """Test user step."""
                    errors = {}
                    if user_input is not None:
                        if user_input.get("abort"):
                            return self.async_abort(reason="abort")

                        errors["entry_id"] = self._config_entry_id
                        try:
                            errors["entry"] = self.config_entry
                        except config_entries.UnknownEntry as err:
                            errors["entry"] = err

                    return self.async_show_form(step_id="init", errors=errors)

            return _OptionsFlow()

    with mock_config_flow("test", TestFlow):
        result = await hass.config_entries.options.async_init(original_entry.entry_id)

    options_flow = hass.config_entries.options._progress.get(result["flow_id"])
    assert isinstance(options_flow, config_entries.OptionsFlow)
    assert options_flow.handler == original_entry.entry_id
    assert isinstance(options_flow.init_entry_id, ValueError)
    assert (
        str(options_flow.init_entry_id)
        == "The config entry id is not available during initialisation"
    )
    assert isinstance(options_flow.init_entry, ValueError)
    assert (
        str(options_flow.init_entry)
        == "The config entry is not available during initialisation"
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert result["errors"] == {}

    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert result["errors"]["entry_id"] == original_entry.entry_id
    assert result["errors"]["entry"] is original_entry

    # Bad handler - not linked to a config entry
    options_flow.handler = "123"
    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert result["errors"]["entry_id"] == "123"
    assert isinstance(result["errors"]["entry"], config_entries.UnknownEntry)
    # Reset handler
    options_flow.handler = original_entry.entry_id

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"abort": True}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "abort"