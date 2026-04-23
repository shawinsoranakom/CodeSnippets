async def test_manual_flow_works(hass: HomeAssistant) -> None:
    """Test config flow discovers only already configured bridges."""
    disc_bridge = get_discovered_bridge(bridge_id="id-1234", host="2.2.2.2")

    MockConfigEntry(
        domain="hue", source=config_entries.SOURCE_IGNORE, unique_id="bla"
    ).add_to_hass(hass)

    with patch(
        "homeassistant.components.hue.config_flow.discover_nupnp",
        return_value=[disc_bridge],
    ):
        result = await hass.config_entries.flow.async_init(
            const.DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"id": "manual"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual"

    with patch.object(config_flow, "discover_bridge", return_value=disc_bridge):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "2.2.2.2"}
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "link"

    with (
        patch.object(config_flow, "create_app_key", return_value="123456789"),
        patch("homeassistant.components.hue.async_unload_entry", return_value=True),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"Hue Bridge {disc_bridge.id}"
    assert result["data"] == {
        "host": "2.2.2.2",
        "api_key": "123456789",
        "api_version": 1,
    }
    entries = hass.config_entries.async_entries("hue")
    assert len(entries) == 2
    entry = entries[-1]
    assert entry.unique_id == "id-1234"