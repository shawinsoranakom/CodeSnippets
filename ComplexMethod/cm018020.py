async def test_unique_id_update_while_setup_in_progress(
    hass: HomeAssistant, manager: config_entries.ConfigEntries
) -> None:
    """Test we handle the case where the config entry is updated while setup is in progress."""

    async def mock_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
        """Mock setting up entry."""
        await asyncio.sleep(0.1)
        return True

    async def mock_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
        """Mock unloading an entry."""
        return True

    hass.config.components.add("comp")
    entry = MockConfigEntry(
        domain="comp",
        data={"additional": "data", "host": "0.0.0.0"},
        unique_id="mock-unique-id",
        state=config_entries.ConfigEntryState.SETUP_RETRY,
    )
    entry.add_to_hass(hass)

    mock_integration(
        hass,
        MockModule(
            "comp",
            async_setup_entry=mock_setup_entry,
            async_unload_entry=mock_unload_entry,
        ),
    )
    mock_platform(hass, "comp.config_flow", None)
    updates = {"host": "1.1.1.1"}

    hass.async_create_task(hass.config_entries.async_reload(entry.entry_id))
    await asyncio.sleep(0)
    assert entry.state is config_entries.ConfigEntryState.SETUP_IN_PROGRESS

    class TestFlow(config_entries.ConfigFlow):
        """Test flow."""

        VERSION = 1

        async def async_step_user(self, user_input=None):
            """Test user step."""
            await self.async_set_unique_id("mock-unique-id")
            await self._abort_if_unique_id_configured(
                updates=updates, reload_on_update=True
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
    assert entry.data["host"] == "1.1.1.1"
    assert entry.data["additional"] == "data"

    # Setup is already in progress, we should not reload
    # if it fails it will go into a retry state and try again
    assert len(async_reload.mock_calls) == 0
    await hass.async_block_till_done()
    assert entry.state is config_entries.ConfigEntryState.LOADED