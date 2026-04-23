async def test_onboarding_integration(
    hass: HomeAssistant,
    hass_storage: dict[str, Any],
    hass_client: ClientSessionGenerator,
    hass_admin_user: MockUser,
) -> None:
    """Test finishing integration step."""
    mock_storage(hass_storage, {"done": [const.STEP_USER]})

    assert await async_setup_component(hass, "onboarding", {})
    await hass.async_block_till_done()

    client = await hass_client()

    resp = await client.post(
        "/api/onboarding/integration",
        json={"client_id": CLIENT_ID, "redirect_uri": CLIENT_REDIRECT_URI},
    )

    assert resp.status == 200
    data = await resp.json()
    assert "auth_code" in data

    # Validate refresh token
    resp = await client.post(
        "/auth/token",
        data={
            "client_id": CLIENT_ID,
            "grant_type": "authorization_code",
            "code": data["auth_code"],
        },
    )

    assert resp.status == 200
    assert const.STEP_INTEGRATION in hass_storage[const.DOMAIN]["data"]["done"]
    tokens = await resp.json()

    assert hass.auth.async_validate_access_token(tokens["access_token"]) is not None

    # Onboarding refresh token and new refresh token
    user = await hass.auth.async_get_user(hass_admin_user.id)
    assert len(user.refresh_tokens) == 2, user