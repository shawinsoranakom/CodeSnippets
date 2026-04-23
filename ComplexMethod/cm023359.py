async def test_set_preferred_border_agent_id(hass: HomeAssistant) -> None:
    """Test set the preferred border agent ID of a dataset."""
    assert await dataset_store.async_get_preferred_dataset(hass) is None

    with pytest.raises(HomeAssistantError):
        await dataset_store.async_add_dataset(
            hass, "source", DATASET_3, preferred_border_agent_id="blah"
        )

    store = await dataset_store.async_get_store(hass)
    assert len(store.datasets) == 0

    with pytest.raises(HomeAssistantError):
        await dataset_store.async_add_dataset(
            hass, "source", DATASET_3, preferred_border_agent_id="bleh"
        )
    assert len(store.datasets) == 0

    await dataset_store.async_add_dataset(hass, "source", DATASET_2)
    assert len(store.datasets) == 1
    assert list(store.datasets.values())[0].preferred_border_agent_id is None

    with pytest.raises(HomeAssistantError):
        await dataset_store.async_add_dataset(
            hass, "source", DATASET_2, preferred_border_agent_id="blah"
        )
    assert list(store.datasets.values())[0].preferred_border_agent_id is None

    store = await dataset_store.async_get_store(hass)
    dataset_id = list(store.datasets.values())[0].id
    with pytest.raises(HomeAssistantError):
        await store.async_set_preferred_border_agent(dataset_id, "blah", None)
    assert list(store.datasets.values())[0].preferred_border_agent_id is None

    await dataset_store.async_add_dataset(hass, "source", DATASET_1)
    assert len(store.datasets) == 2
    assert list(store.datasets.values())[1].preferred_border_agent_id is None

    with pytest.raises(HomeAssistantError):
        await dataset_store.async_add_dataset(
            hass, "source", DATASET_1_LARGER_TIMESTAMP, preferred_border_agent_id="blah"
        )
    assert list(store.datasets.values())[1].preferred_border_agent_id is None