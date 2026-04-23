async def test_configurator(
    hass: HomeAssistant,
    client: MagicMock,
    storage: MagicMock,
    configure_id: str,
    token: str | None,
    rtm_entity_exists: bool,
    configurator_end_state: str,
) -> None:
    """Test configurator."""
    storage.get_token.return_value = None
    client.authenticate_desktop.return_value = ("test-url", "test-frob")
    client.token = token
    rtm_entity_id = f"{DOMAIN}.{PROFILE}"
    configure_entity_id = f"configurator.{DOMAIN}_{PROFILE}"

    assert await async_setup_component(hass, DOMAIN, {DOMAIN: CONFIG})
    await hass.async_block_till_done()

    assert hass.states.get(rtm_entity_id) is None
    state = hass.states.get(configure_entity_id)
    assert state
    assert state.state == "configure"

    await hass.services.async_call(
        "configurator",
        "configure",
        {"configure_id": configure_id},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert bool(hass.states.get(rtm_entity_id)) == rtm_entity_exists
    state = hass.states.get(configure_entity_id)
    assert state
    assert state.state == configurator_end_state