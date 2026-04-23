async def test_registration(
    hass: HomeAssistant, hass_client: ClientSessionGenerator, hass_admin_user: MockUser
) -> None:
    """Test that registrations happen."""
    await async_setup_component(hass, DOMAIN, {DOMAIN: {}})

    api_client = await hass_client()

    with patch(
        "homeassistant.components.person.async_add_user_device_tracker",
        spec=True,
    ) as add_user_dev_track:
        resp = await api_client.post(
            "/api/mobile_app/registrations", json=REGISTER_CLEARTEXT
        )

    assert len(add_user_dev_track.mock_calls) == 1
    assert add_user_dev_track.mock_calls[0][1][1] == hass_admin_user.id
    assert add_user_dev_track.mock_calls[0][1][2] == "device_tracker.test_1"

    assert resp.status == HTTPStatus.CREATED
    register_json = await resp.json()
    assert CONF_WEBHOOK_ID in register_json
    assert CONF_SECRET in register_json

    entries = hass.config_entries.async_entries(DOMAIN)

    assert entries[0].unique_id == "io.homeassistant.mobile_app_test-mock-device-id"
    assert entries[0].data["device_id"] == REGISTER_CLEARTEXT["device_id"]
    assert entries[0].data["app_data"] == REGISTER_CLEARTEXT["app_data"]
    assert entries[0].data["app_id"] == REGISTER_CLEARTEXT["app_id"]
    assert entries[0].data["app_name"] == REGISTER_CLEARTEXT["app_name"]
    assert entries[0].data["app_version"] == REGISTER_CLEARTEXT["app_version"]
    assert entries[0].data["device_name"] == REGISTER_CLEARTEXT["device_name"]
    assert entries[0].data["manufacturer"] == REGISTER_CLEARTEXT["manufacturer"]
    assert entries[0].data["model"] == REGISTER_CLEARTEXT["model"]
    assert entries[0].data["os_name"] == REGISTER_CLEARTEXT["os_name"]
    assert entries[0].data["os_version"] == REGISTER_CLEARTEXT["os_version"]
    assert (
        entries[0].data["supports_encryption"]
        == REGISTER_CLEARTEXT["supports_encryption"]
    )