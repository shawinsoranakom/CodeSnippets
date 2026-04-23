async def test_change_api_5_to_6(
    hass: HomeAssistant, issue_registry: ir.IssueRegistry
) -> None:
    """Tests a user with an API version 5 config entry that is updated to API version 6."""
    mocked_hole = _create_mocked_hole(api_version=5)

    # setu up a valid API version 5 config entry
    entry = MockConfigEntry(
        domain=pi_hole.DOMAIN,
        data={**CONFIG_DATA_DEFAULTS, CONF_API_VERSION: 5},
    )
    entry.add_to_hass(hass)
    with _patch_init_hole(mocked_hole):
        assert await hass.config_entries.async_setup(entry.entry_id)

        assert mocked_hole.instances[-1].data == ZERO_DATA
        # Change the mock's state after setup
        mocked_hole.instances[-1].hole_version = 6
        mocked_hole.instances[-1].api_token = "wrong_token"

        # Patch the method on the coordinator's api reference directly
        pihole_data = entry.runtime_data
        assert pihole_data.api == mocked_hole.instances[-1]
        pihole_data.api.get_data = AsyncMock(
            side_effect=lambda: setattr(
                pihole_data.api,
                "data",
                {"error": VERSION_6_RESPONSE_TO_5_ERROR, "took": 0.0001430511474609375},
            )
        )

        # Now trigger the update
        with pytest.raises(homeassistant.exceptions.ConfigEntryAuthFailed):
            await pihole_data.coordinator._async_update_data()
        assert pihole_data.api.data == {
            "error": VERSION_6_RESPONSE_TO_5_ERROR,
            "took": 0.0001430511474609375,
        }

        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=10))
        await hass.async_block_till_done()
        # ensure a re-auth flow is created
        flows = hass.config_entries.flow.async_progress()
        assert len(flows) == 1
        assert flows[0]["step_id"] == "reauth_confirm"
        assert flows[0]["context"]["entry_id"] == entry.entry_id