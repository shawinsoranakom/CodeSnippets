async def test_update_subentry_and_abort(
    hass: HomeAssistant,
    expected_title: str,
    expected_unique_id: str,
    expected_data: dict[str, Any],
    kwargs: dict[str, Any],
    raises: type[Exception] | None,
) -> None:
    """Test updating an entry and reloading."""
    subentry_id = "blabla"
    entry = MockConfigEntry(
        domain="comp",
        unique_id="entry_unique_id",
        title="entry_title",
        data={},
        subentries_data=[
            config_entries.ConfigSubentryData(
                data={"vendor": "data"},
                subentry_id=subentry_id,
                subentry_type="test",
                unique_id="1234",
                title="Test",
            )
        ],
    )
    entry.add_to_hass(hass)
    subentry = entry.subentries[subentry_id]

    comp = MockModule("comp")
    mock_integration(hass, comp)
    mock_platform(hass, "comp.config_flow", None)

    class TestFlow(config_entries.ConfigFlow):
        class SubentryFlowHandler(config_entries.ConfigSubentryFlow):
            async def async_step_reconfigure(self, user_input=None):
                return self.async_update_and_abort(
                    self._get_entry(),
                    self._get_reconfigure_subentry(),
                    **kwargs,
                )

        @classmethod
        @callback
        def async_get_supported_subentry_types(
            cls, config_entry: config_entries.ConfigEntry
        ) -> dict[str, type[config_entries.ConfigSubentryFlow]]:
            return {"test": TestFlow.SubentryFlowHandler}

    err: Exception
    with mock_config_flow("comp", TestFlow):
        try:
            result = await entry.start_subentry_reconfigure_flow(hass, subentry_id)
        except Exception as ex:  # noqa: BLE001
            err = ex

    await hass.async_block_till_done()

    subentry = entry.subentries[subentry_id]
    assert subentry.title == expected_title
    assert subentry.unique_id == expected_unique_id
    assert subentry.data == expected_data
    if raises:
        assert isinstance(err, raises)
    else:
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "reconfigure_successful"