async def test_unique_id_ignore(
    hass: HomeAssistant,
    manager: config_entries.ConfigEntries,
    extra_context: dict,
    expected_entry_discovery_keys: dict,
) -> None:
    """Test that we can ignore flows that are in progress and have a unique ID."""
    async_setup_entry = AsyncMock(return_value=False)
    mock_integration(hass, MockModule("comp", async_setup_entry=async_setup_entry))
    mock_platform(hass, "comp.config_flow", None)

    class TestFlow(config_entries.ConfigFlow):
        """Test flow."""

        VERSION = 1

        async def async_step_user(self, user_input=None):
            """Test user flow."""
            await self.async_set_unique_id("mock-unique-id")
            return self.async_show_form(step_id="discovery")

    with mock_config_flow("comp", TestFlow):
        # Create one to be in progress
        result = await manager.flow.async_init(
            "comp", context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == data_entry_flow.FlowResultType.FORM

        result2 = await manager.flow.async_init(
            "comp",
            context={"source": config_entries.SOURCE_IGNORE} | extra_context,
            data={"unique_id": "mock-unique-id", "title": "Ignored Title"},
        )

    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY

    # assert len(hass.config_entries.flow.async_progress()) == 0

    # We should never set up an ignored entry.
    assert len(async_setup_entry.mock_calls) == 0

    entry = hass.config_entries.async_entries("comp")[0]

    assert entry.source == "ignore"
    assert entry.unique_id == "mock-unique-id"
    assert entry.title == "Ignored Title"
    assert entry.data == {}
    assert entry.discovery_keys == expected_entry_discovery_keys