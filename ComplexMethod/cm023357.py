async def test_dataset_properties(hass: HomeAssistant) -> None:
    """Test dataset entry properties."""
    datasets = [
        {"source": "Google", "tlv": DATASET_1},
        {"source": "Multipan", "tlv": DATASET_2},
        {"source": "🎅", "tlv": DATASET_3},
        {"source": "test2", "tlv": DATASET_1_NO_CHANNEL},
    ]

    for dataset in datasets:
        await dataset_store.async_add_dataset(hass, dataset["source"], dataset["tlv"])

    store = await dataset_store.async_get_store(hass)
    for dataset in store.datasets.values():
        if dataset.source == "Google":
            dataset_1 = dataset
        if dataset.source == "Multipan":
            dataset_2 = dataset
        if dataset.source == "🎅":
            dataset_3 = dataset
        if dataset.source == "test2":
            dataset_4 = dataset

    dataset = store.async_get(dataset_1.id)
    assert dataset == dataset_1
    assert dataset.channel == 15
    assert dataset.extended_pan_id == "1111111122222222"
    assert dataset.network_name == "OpenThreadDemo"
    assert dataset.pan_id == "1234"

    dataset = store.async_get(dataset_2.id)
    assert dataset == dataset_2
    assert dataset.channel == 15
    assert dataset.extended_pan_id == "1111111122222233"
    assert dataset.network_name == "HomeAssistant!"
    assert dataset.pan_id == "1234"

    dataset = store.async_get(dataset_3.id)
    assert dataset == dataset_3
    assert dataset.channel == 15
    assert dataset.extended_pan_id == "1111111122222244"
    assert dataset.network_name == "~🐣🐥🐤~"
    assert dataset.pan_id == "1234"

    dataset = store.async_get(dataset_4.id)
    assert dataset == dataset_4
    assert dataset.channel is None