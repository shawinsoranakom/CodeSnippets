async def test_list_get_dataset(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test list and get datasets."""
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)

    await client.send_json({"id": 1, "type": "thread/list_datasets"})
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] == {"datasets": []}

    datasets = [
        {"source": "Google", "tlv": DATASET_1},
        {"source": "Multipan", "tlv": DATASET_2},
        {"source": "🎅", "tlv": DATASET_3},
    ]
    for dataset in datasets:
        await dataset_store.async_add_dataset(hass, dataset["source"], dataset["tlv"])

    store = await dataset_store.async_get_store(hass)
    dataset_id = list(store.datasets.values())[0].id
    store.preferred_dataset = dataset_id

    for dataset in store.datasets.values():
        if dataset.source == "Google":
            dataset_1 = dataset
        if dataset.source == "Multipan":
            dataset_2 = dataset
        if dataset.source == "🎅":
            dataset_3 = dataset

    await client.send_json({"id": 2, "type": "thread/list_datasets"})
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] == {
        "datasets": [
            {
                "channel": 15,
                "created": dataset_1.created.isoformat(),
                "dataset_id": dataset_1.id,
                "extended_pan_id": "1111111122222222",
                "network_name": "OpenThreadDemo",
                "pan_id": "1234",
                "preferred": True,
                "preferred_border_agent_id": None,
                "preferred_extended_address": None,
                "source": "Google",
            },
            {
                "channel": 15,
                "created": dataset_2.created.isoformat(),
                "dataset_id": dataset_2.id,
                "extended_pan_id": "1111111122222233",
                "network_name": "HomeAssistant!",
                "pan_id": "1234",
                "preferred": False,
                "preferred_border_agent_id": None,
                "preferred_extended_address": None,
                "source": "Multipan",
            },
            {
                "channel": 15,
                "created": dataset_3.created.isoformat(),
                "dataset_id": dataset_3.id,
                "extended_pan_id": "1111111122222244",
                "network_name": "~🐣🐥🐤~",
                "pan_id": "1234",
                "preferred": False,
                "preferred_border_agent_id": None,
                "preferred_extended_address": None,
                "source": "🎅",
            },
        ]
    }

    await client.send_json(
        {"id": 3, "type": "thread/get_dataset_tlv", "dataset_id": dataset_2.id}
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] == {"tlv": dataset_2.tlv}

    await client.send_json(
        {"id": 4, "type": "thread/get_dataset_tlv", "dataset_id": "blah"}
    )
    msg = await client.receive_json()
    assert not msg["success"]
    assert msg["error"] == {"code": "not_found", "message": "unknown dataset"}