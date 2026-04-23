async def test_complete_onboarding(
    hass: HomeAssistant, hass_client: ClientSessionGenerator
) -> None:
    """Test completing onboarding calls listeners."""
    listener_1 = Mock()
    onboarding.async_add_listener(hass, listener_1)
    listener_1.assert_not_called()

    assert await async_setup_component(hass, "onboarding", {})
    await hass.async_block_till_done()

    listener_2 = Mock()
    onboarding.async_add_listener(hass, listener_2)
    listener_2.assert_not_called()

    client = await hass_client()

    assert not onboarding.async_is_onboarded(hass)

    # Complete the user step
    resp = await client.post(
        "/api/onboarding/users",
        json={
            "client_id": CLIENT_ID,
            "name": "Test Name",
            "username": "test-user",
            "password": "test-pass",
            "language": "en",
        },
    )
    assert resp.status == 200
    assert not onboarding.async_is_onboarded(hass)
    listener_2.assert_not_called()

    # Complete the core config step
    resp = await client.post("/api/onboarding/core_config")
    assert resp.status == 200
    assert not onboarding.async_is_onboarded(hass)
    listener_2.assert_not_called()

    # Complete the integration step
    resp = await client.post(
        "/api/onboarding/integration",
        json={"client_id": CLIENT_ID, "redirect_uri": CLIENT_REDIRECT_URI},
    )
    assert resp.status == 200
    assert not onboarding.async_is_onboarded(hass)
    listener_2.assert_not_called()

    # Complete the analytics step
    resp = await client.post("/api/onboarding/analytics")
    assert resp.status == 200
    assert onboarding.async_is_onboarded(hass)
    listener_1.assert_not_called()  # Registered before the integration was setup
    listener_2.assert_called_once_with()

    listener_3 = Mock()
    onboarding.async_add_listener(hass, listener_3)
    listener_3.assert_called_once_with()