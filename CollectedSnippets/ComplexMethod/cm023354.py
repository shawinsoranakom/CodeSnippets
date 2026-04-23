async def test_set_preferred_border_agent(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test setting the preferred border agent ID."""
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {"type": "thread/add_dataset_tlv", "source": "test", "tlv": DATASET_1}
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] is None

    await client.send_json_auto_id({"type": "thread/list_datasets"})
    msg = await client.receive_json()
    assert msg["success"]
    datasets = msg["result"]["datasets"]
    dataset_id = datasets[0]["dataset_id"]
    assert datasets[0]["preferred_border_agent_id"] is None
    assert datasets[0]["preferred_extended_address"] is None

    await client.send_json_auto_id(
        {
            "type": "thread/set_preferred_border_agent",
            "dataset_id": dataset_id,
            "border_agent_id": "blah",
            "extended_address": "bleh",
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] is None

    await client.send_json_auto_id({"type": "thread/list_datasets"})
    msg = await client.receive_json()
    assert msg["success"]
    datasets = msg["result"]["datasets"]
    assert datasets[0]["preferred_border_agent_id"] == "blah"
    assert datasets[0]["preferred_extended_address"] == "bleh"