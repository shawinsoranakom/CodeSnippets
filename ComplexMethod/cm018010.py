async def test_unique_id_update_existing_entry_with_reload(
    hass: HomeAssistant, manager: config_entries.ConfigEntries
) -> None:
    """Test that we update an entry if there already is an entry with unique ID and we reload on changes."""
    hass.config.components.add("comp")
    entry = MockConfigEntry(
        domain="comp",
        data={"additional": "data", "host": "0.0.0.0"},
        unique_id="mock-unique-id",
        state=config_entries.ConfigEntryState.LOADED,
    )
    entry.add_to_hass(hass)

    mock_integration(
        hass,
        MockModule("comp"),
    )
    mock_platform(hass, "comp.config_flow", None)
    updates = {"host": "1.1.1.1"}

    class TestFlow(config_entries.ConfigFlow):
        """Test flow."""

        VERSION = 1

        async def async_step_user(self, user_input=None):
            """Test user step."""
            await self.async_set_unique_id("mock-unique-id")
            await self._abort_if_unique_id_configured(
                updates=updates,
                reload_on_update=True,
                description_placeholders={"title": "Other device"},
            )

    with (
        mock_config_flow("comp", TestFlow),
        patch(
            "homeassistant.config_entries.ConfigEntries.async_reload"
        ) as async_reload,
    ):
        result = await manager.flow.async_init(
            "comp", context={"source": config_entries.SOURCE_USER}
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert result["description_placeholders"]["title"] == "Other device"
    assert entry.data["host"] == "1.1.1.1"
    assert entry.data["additional"] == "data"
    assert len(async_reload.mock_calls) == 1

    # Test we don't reload if entry not started
    updates["host"] = "2.2.2.2"
    entry._async_set_state(hass, config_entries.ConfigEntryState.NOT_LOADED, None)
    with (
        mock_config_flow("comp", TestFlow),
        patch(
            "homeassistant.config_entries.ConfigEntries.async_reload"
        ) as async_reload,
    ):
        result = await manager.flow.async_init(
            "comp", context={"source": config_entries.SOURCE_USER}
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert result["description_placeholders"]["title"] == "Other device"
    assert entry.data["host"] == "2.2.2.2"
    assert entry.data["additional"] == "data"
    assert len(async_reload.mock_calls) == 0