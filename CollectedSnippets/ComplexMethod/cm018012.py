async def test_flow_with_default_discovery(
    hass: HomeAssistant,
    manager: config_entries.ConfigEntries,
    discovery_source: tuple[str, dict | BaseServiceInfo],
) -> None:
    """Test that finishing a default discovery flow removes the unique ID in the entry."""
    mock_integration(
        hass,
        MockModule("comp", async_setup_entry=AsyncMock(return_value=True)),
    )
    mock_platform(hass, "comp.config_flow", None)

    class TestFlow(config_entries.ConfigFlow):
        """Test flow."""

        VERSION = 1

        async def async_step_user(self, user_input=None):
            """Test user step."""
            if user_input is None:
                return self.async_show_form(step_id="user")

            return self.async_create_entry(title="yo", data={})

    with mock_config_flow("comp", TestFlow):
        # Create one to be in progress
        result = await manager.flow.async_init(
            "comp", context={"source": discovery_source[0]}, data=discovery_source[1]
        )
        assert result["type"] == data_entry_flow.FlowResultType.FORM

        flows = hass.config_entries.flow.async_progress()
        assert len(flows) == 1
        assert (
            flows[0]["context"]["unique_id"]
            == config_entries.DEFAULT_DISCOVERY_UNIQUE_ID
        )

        # Finish flow
        result2 = await manager.flow.async_configure(
            result["flow_id"], user_input={"fake": "data"}
        )
        assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY

    assert len(hass.config_entries.flow.async_progress()) == 0

    entry = hass.config_entries.async_entries("comp")[0]
    assert entry.title == "yo"
    assert entry.source == discovery_source[0]
    assert entry.unique_id is None