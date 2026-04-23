async def test_load_datasets(hass: HomeAssistant) -> None:
    """Make sure that we can load/save data correctly."""

    datasets = [
        {
            "source": "Google",
            "tlv": DATASET_1,
        },
        {
            "source": "Multipan",
            "tlv": DATASET_2,
        },
        {
            "source": "🎅",
            "tlv": DATASET_3,
        },
    ]

    store1 = await dataset_store.async_get_store(hass)
    for dataset in datasets:
        store1.async_add(dataset["source"], dataset["tlv"], None, None)
    assert len(store1.datasets) == 3
    dataset_id = list(store1.datasets.values())[0].id
    store1.preferred_dataset = dataset_id

    for dataset in store1.datasets.values():
        if dataset.source == "Google":
            dataset_1_store_1 = dataset
        if dataset.source == "Multipan":
            dataset_2_store_1 = dataset
        if dataset.source == "🎅":
            dataset_3_store_1 = dataset

    assert store1.preferred_dataset == dataset_1_store_1.id

    with pytest.raises(HomeAssistantError):
        store1.async_delete(dataset_1_store_1.id)
    store1.async_delete(dataset_2_store_1.id)

    assert len(store1.datasets) == 2

    store2 = dataset_store.DatasetStore(hass)
    await flush_store(store1._store)
    await store2.async_load()

    assert len(store2.datasets) == 2

    for dataset in store2.datasets.values():
        if dataset.source == "Google":
            dataset_1_store_2 = dataset
        if dataset.source == "🎅":
            dataset_3_store_2 = dataset

    assert list(store1.datasets) == list(store2.datasets)

    assert dataset_1_store_1 == dataset_1_store_2
    assert dataset_3_store_1 == dataset_3_store_2