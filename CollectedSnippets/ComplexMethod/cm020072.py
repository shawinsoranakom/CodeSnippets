async def test_options_flow(hass: HomeAssistant) -> None:
    """Test we can edit options."""

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={
            CONF_HOSTS_LIST: ["192.168.1.0/24"],
            CONF_HOME_INTERVAL: 3,
            CONF_OPTIONS: DEFAULT_OPTIONS,
            CONF_HOSTS_EXCLUDE: ["4.4.4.4"],
            CONF_MAC_EXCLUDE: ["00:00:00:00:00:00", "11:22:33:44:55:66"],
        },
        version=1,
        minor_version=2,
    )
    config_entry.add_to_hass(hass)
    hass.set_state(CoreState.stopped)

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    assert result["data_schema"]({}) == {
        CONF_HOSTS_EXCLUDE: ["4.4.4.4"],
        CONF_HOME_INTERVAL: 3,
        CONF_HOSTS_LIST: ["192.168.1.0/24"],
        CONF_CONSIDER_HOME: 180,
        CONF_SCAN_INTERVAL: 120,
        CONF_OPTIONS: "-n -sn -PR -T4 --min-rate 10 --host-timeout 5s",
        CONF_MAC_EXCLUDE: ["00:00:00:00:00:00", "11:22:33:44:55:66"],
    }

    with patch(
        "homeassistant.components.nmap_tracker.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOSTS_LIST: ["192.168.1.0/24", "192.168.2.0/24"],
                CONF_HOME_INTERVAL: 5,
                CONF_CONSIDER_HOME: 500,
                CONF_OPTIONS: "-sn",
                CONF_HOSTS_EXCLUDE: ["4.4.4.4", "5.5.5.5"],
                CONF_SCAN_INTERVAL: 10,
                CONF_MAC_EXCLUDE: ["00:00:00:00:00:00", "11:22:33:44:55:66"],
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options == {
        CONF_HOSTS_LIST: ["192.168.1.0/24", "192.168.2.0/24"],
        CONF_HOME_INTERVAL: 5,
        CONF_CONSIDER_HOME: 500,
        CONF_OPTIONS: "-sn",
        CONF_HOSTS_EXCLUDE: ["4.4.4.4", "5.5.5.5"],
        CONF_SCAN_INTERVAL: 10,
        CONF_MAC_EXCLUDE: ["00:00:00:00:00:00", "11:22:33:44:55:66"],
    }
    assert len(mock_setup_entry.mock_calls) == 1