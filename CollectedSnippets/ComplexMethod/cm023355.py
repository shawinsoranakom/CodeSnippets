async def test_set_preferred_dataset(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test we set a dataset as default."""
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    datasets = [
        {"source": "Google", "tlv": DATASET_1},
        {"source": "Multipan", "tlv": DATASET_2},
        {"source": "🎅", "tlv": DATASET_3},
    ]
    for dataset in datasets:
        await dataset_store.async_add_dataset(hass, dataset["source"], dataset["tlv"])

    store = await dataset_store.async_get_store(hass)

    for dataset in store.datasets.values():
        if dataset.source == "🎅":
            dataset_3 = dataset

    client = await hass_ws_client(hass)

    await client.send_json(
        {"id": 1, "type": "thread/set_preferred_dataset", "dataset_id": dataset_3.id}
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] is None

    store = await dataset_store.async_get_store(hass)
    assert store.preferred_dataset == dataset_3.id