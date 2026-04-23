async def test_import(hass: HomeAssistant) -> None:
    """Test we can import instance."""

    ignored_entry = MockConfigEntry(domain=DOMAIN, data={}, source=SOURCE_IGNORE)
    ignored_entry.add_to_hass(hass)
    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_NAME: "mock_name", CONF_PORT: 12345}
    )
    entry.add_to_hass(hass)
    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data={CONF_NAME: "mock_name", CONF_PORT: 12345},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "port_name_in_use"

    with (
        patch(
            "homeassistant.components.homekit.async_setup", return_value=True
        ) as mock_setup,
        patch(
            "homeassistant.components.homekit.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={CONF_NAME: "othername", CONF_PORT: 56789},
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "othername:56789"
    assert result2["data"] == {
        "name": "othername",
        "port": 56789,
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 2