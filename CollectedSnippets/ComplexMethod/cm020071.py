async def test_form_range(hass: HomeAssistant) -> None:
    """Test we get the form and can take an ip range."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.nmap_tracker.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOSTS_LIST: ["192.168.0.5-12"],
                CONF_HOME_INTERVAL: 3,
                CONF_OPTIONS: DEFAULT_OPTIONS,
                CONF_HOSTS_EXCLUDE: ["4.4.4.4"],
                CONF_MAC_EXCLUDE: ["00:00:00:00:00:00"],
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Nmap Tracker 192.168.0.5-12"
    assert result2["data"] == {}
    assert result2["options"] == {
        CONF_HOSTS_LIST: ["192.168.0.5-12"],
        CONF_HOME_INTERVAL: 3,
        CONF_OPTIONS: DEFAULT_OPTIONS,
        CONF_HOSTS_EXCLUDE: ["4.4.4.4"],
        CONF_MAC_EXCLUDE: ["00:00:00:00:00:00"],
    }
    assert len(mock_setup_entry.mock_calls) == 1