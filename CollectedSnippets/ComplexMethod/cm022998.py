async def test_config_flow_preview(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test the config flow preview."""
    client = await hass_ws_client(hass)
    freezer.move_to("2024-01-02 20:14:11.672")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] is None
    assert result["preview"] == "time_date"

    await client.send_json_auto_id(
        {
            "type": "time_date/start_preview",
            "flow_id": result["flow_id"],
            "flow_type": "config_flow",
            "user_input": {"display_options": "time"},
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] is None

    msg = await client.receive_json()
    assert msg["event"] == {
        "attributes": {"friendly_name": "Time", "icon": "mdi:clock"},
        "state": "12:14",
    }

    freezer.tick(60)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    msg = await client.receive_json()
    assert msg["event"] == {
        "attributes": {"friendly_name": "Time", "icon": "mdi:clock"},
        "state": "12:15",
    }
    assert len(hass.states.async_all()) == 0