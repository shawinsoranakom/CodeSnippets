async def test_setup_in_bridge_mode_name_taken(hass: HomeAssistant) -> None:
    """Test we can setup a new instance in bridge mode when the name is taken."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_NAME: SHORT_BRIDGE_NAME, CONF_PORT: 8000},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"include_domains": ["light"]},
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "pairing"

    with (
        patch(
            "homeassistant.components.homekit.config_flow.async_find_next_available_port",
            return_value=12345,
        ),
        patch(
            "homeassistant.components.homekit.async_setup", return_value=True
        ) as mock_setup,
        patch(
            "homeassistant.components.homekit.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] != SHORT_BRIDGE_NAME
    assert result3["title"].startswith(SHORT_BRIDGE_NAME)
    bridge_name = (result3["title"].split(":"))[0]
    assert result3["data"] == {
        "filter": {
            "exclude_domains": [],
            "exclude_entities": [],
            "include_domains": ["light"],
            "include_entities": [],
        },
        "exclude_accessory_mode": True,
        "mode": "bridge",
        "name": bridge_name,
        "port": 12345,
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 2