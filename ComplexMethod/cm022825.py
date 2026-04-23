async def test_setup(hass: HomeAssistant, fritz: Mock) -> None:
    """Test setup of integration."""
    assert await setup_config_entry(hass, MOCK_CONFIG[DOMAIN][CONF_DEVICES][0])
    entries = hass.config_entries.async_entries()
    assert entries
    assert len(entries) == 1
    assert entries[0].data[CONF_HOST] == "10.0.0.1"
    assert entries[0].data[CONF_PASSWORD] == "fake_pass"
    assert entries[0].data[CONF_USERNAME] == "fake_user"
    assert fritz.call_count == 1
    assert fritz.call_args_list == [
        call(host="10.0.0.1", password="fake_pass", user="fake_user", timeout=20)
    ]