async def test_set_preferred_border_agent_id_and_extended_address(
    hass: HomeAssistant,
) -> None:
    """Test set the preferred border agent ID and extended address of a dataset."""
    assert await dataset_store.async_get_preferred_dataset(hass) is None

    await dataset_store.async_add_dataset(
        hass,
        "source",
        DATASET_3,
        preferred_border_agent_id="blah",
        preferred_extended_address="bleh",
    )

    store = await dataset_store.async_get_store(hass)
    assert len(store.datasets) == 1
    assert list(store.datasets.values())[0].preferred_border_agent_id == "blah"
    assert list(store.datasets.values())[0].preferred_extended_address == "bleh"

    await dataset_store.async_add_dataset(
        hass,
        "source",
        DATASET_3,
        preferred_border_agent_id="bleh",
        preferred_extended_address="bleh",
    )
    assert list(store.datasets.values())[0].preferred_border_agent_id == "blah"
    assert list(store.datasets.values())[0].preferred_extended_address == "bleh"

    await dataset_store.async_add_dataset(hass, "source", DATASET_2)
    assert len(store.datasets) == 2
    assert list(store.datasets.values())[1].preferred_border_agent_id is None
    assert list(store.datasets.values())[1].preferred_extended_address is None

    await dataset_store.async_add_dataset(
        hass,
        "source",
        DATASET_2,
        preferred_border_agent_id="blah",
        preferred_extended_address="bleh",
    )
    assert list(store.datasets.values())[1].preferred_border_agent_id == "blah"
    assert list(store.datasets.values())[1].preferred_extended_address == "bleh"

    await dataset_store.async_add_dataset(hass, "source", DATASET_1)
    assert len(store.datasets) == 3
    assert list(store.datasets.values())[2].preferred_border_agent_id is None
    assert list(store.datasets.values())[2].preferred_extended_address is None

    await dataset_store.async_add_dataset(
        hass,
        "source",
        DATASET_1_LARGER_TIMESTAMP,
        preferred_border_agent_id="blah",
        preferred_extended_address="bleh",
    )
    assert list(store.datasets.values())[2].preferred_border_agent_id == "blah"
    assert list(store.datasets.values())[2].preferred_extended_address == "bleh"