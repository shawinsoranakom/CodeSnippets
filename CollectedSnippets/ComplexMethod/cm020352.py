async def test_app_password_changing(
    hass: HomeAssistant, issue_registry: ir.IssueRegistry
) -> None:
    """Tests a user with an API version 5 config entry that is updated to API version 6."""
    mocked_hole = _create_mocked_hole(
        api_version=6, has_data=True, incorrect_app_password=False
    )
    entry = MockConfigEntry(domain=pi_hole.DOMAIN, data={**CONFIG_DATA_DEFAULTS})
    entry.add_to_hass(hass)
    with _patch_init_hole(mocked_hole):
        assert await hass.config_entries.async_setup(entry.entry_id)

    state = hass.states.get("sensor.pi_hole_ads_blocked")
    assert state is not None
    assert state.name == "Pi-Hole Ads blocked"
    assert state.state == "0"

    # Test app password changing
    async def fail_auth():
        """Set mocked data to bad_data."""
        raise HoleError("Authentication failed: Invalid password")

    mocked_hole.instances[-1].get_data = AsyncMock(side_effect=fail_auth)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=10))
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    assert flows[0]["step_id"] == "reauth_confirm"
    assert flows[0]["context"]["entry_id"] == entry.entry_id

    # Test app password changing
    async def fail_fetch():
        """Set mocked data to bad_data."""
        raise HoleConnectionError("Cannot fetch data from Pi-hole: 200")

    mocked_hole.instances[-1].get_data = AsyncMock(side_effect=fail_fetch)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=10))
    await hass.async_block_till_done()