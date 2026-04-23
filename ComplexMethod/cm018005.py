async def test_create_entry_subentries(
    hass: HomeAssistant, manager: config_entries.ConfigEntries
) -> None:
    """Test a config entry being created with subentries."""

    subentrydata = config_entries.ConfigSubentryData(
        data={"test": "test"},
        title="Mock title",
        subentry_type="test",
        unique_id="test",
    )

    async def mock_async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
        """Mock setup."""
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                "comp",
                context={"source": config_entries.SOURCE_IMPORT},
                data={"data": "data", "subentry": subentrydata},
            )
        )
        return True

    async_setup_entry = AsyncMock(return_value=True)
    mock_integration(
        hass,
        MockModule(
            "comp", async_setup=mock_async_setup, async_setup_entry=async_setup_entry
        ),
    )
    mock_platform(hass, "comp.config_flow", None)

    class TestFlow(config_entries.ConfigFlow):
        """Test flow."""

        VERSION = 1

        async def async_step_import(self, user_input):
            """Test import step creating entry, with subentry."""
            return self.async_create_entry(
                title="title",
                data={"example": user_input["data"]},
                subentries=[user_input["subentry"]],
            )

    with patch.dict(config_entries.HANDLERS, {"comp": TestFlow}):
        assert await async_setup_component(hass, "comp", {})

        await hass.async_block_till_done()

        assert len(async_setup_entry.mock_calls) == 1

        entries = hass.config_entries.async_entries("comp")
        assert len(entries) == 1
        assert entries[0].supported_subentry_types == {}
        assert entries[0].data == {"example": "data"}
        assert len(entries[0].subentries) == 1
        subentry_id = list(entries[0].subentries)[0]
        subentry = config_entries.ConfigSubentry(
            data=subentrydata["data"],
            subentry_id=subentry_id,
            subentry_type="test",
            title=subentrydata["title"],
            unique_id="test",
        )
        assert entries[0].subentries == {subentry_id: subentry}