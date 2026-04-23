async def test_button_dismiss_current_notification(
    hass: HomeAssistant,
    mock_lametric: MagicMock,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test the LaMetric dismiss current notification button."""
    state = hass.states.get("button.frenck_s_lametric_dismiss_current_notification")
    assert state
    assert state.state == STATE_UNKNOWN

    entry = entity_registry.async_get(
        "button.frenck_s_lametric_dismiss_current_notification"
    )
    assert entry
    assert entry.unique_id == "SA110405124500W00BS9-dismiss_current"
    assert entry.entity_category == EntityCategory.CONFIG

    assert entry.device_id
    device_entry = device_registry.async_get(entry.device_id)
    assert device_entry
    assert device_entry.configuration_url == "https://127.0.0.1/"
    assert device_entry.connections == {
        (dr.CONNECTION_NETWORK_MAC, "aa:bb:cc:dd:ee:ff"),
        (dr.CONNECTION_BLUETOOTH, "aa:bb:cc:dd:ee:ee"),
    }
    assert device_entry.entry_type is None
    assert device_entry.identifiers == {(DOMAIN, "SA110405124500W00BS9")}
    assert device_entry.manufacturer == "LaMetric Inc."
    assert device_entry.model_id == "LM 37X8"
    assert device_entry.name == "Frenck's LaMetric"
    assert device_entry.sw_version == "2.2.2"
    assert device_entry.hw_version is None

    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: "button.frenck_s_lametric_dismiss_current_notification"},
        blocking=True,
    )

    assert len(mock_lametric.dismiss_current_notification.mock_calls) == 1
    mock_lametric.dismiss_current_notification.assert_called_with()

    state = hass.states.get("button.frenck_s_lametric_dismiss_current_notification")
    assert state
    assert state.state == "2022-09-19T12:07:30+00:00"