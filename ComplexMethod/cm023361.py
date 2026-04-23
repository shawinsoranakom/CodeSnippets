async def test_set_preferred_extended_address(hass: HomeAssistant) -> None:
    """Test set the preferred extended address of a dataset."""
    assert await dataset_store.async_get_preferred_dataset(hass) is None

    await dataset_store.async_add_dataset(
        hass, "source", DATASET_3, preferred_extended_address="blah"
    )

    store = await dataset_store.async_get_store(hass)
    assert len(store.datasets) == 1
    assert list(store.datasets.values())[0].preferred_extended_address == "blah"

    await dataset_store.async_add_dataset(
        hass, "source", DATASET_3, preferred_extended_address="bleh"
    )
    assert list(store.datasets.values())[0].preferred_extended_address == "blah"

    await dataset_store.async_add_dataset(hass, "source", DATASET_2)
    assert len(store.datasets) == 2
    assert list(store.datasets.values())[1].preferred_extended_address is None

    await dataset_store.async_add_dataset(
        hass, "source", DATASET_2, preferred_extended_address="blah"
    )
    assert list(store.datasets.values())[1].preferred_extended_address == "blah"

    await dataset_store.async_add_dataset(hass, "source", DATASET_1)
    assert len(store.datasets) == 3
    assert list(store.datasets.values())[2].preferred_extended_address is None

    await dataset_store.async_add_dataset(
        hass, "source", DATASET_1_LARGER_TIMESTAMP, preferred_extended_address="blah"
    )
    assert list(store.datasets.values())[2].preferred_extended_address == "blah"