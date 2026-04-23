async def test_delete_script(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    entity_registry: er.EntityRegistry,
    hass_config_store: dict[str, Any],
) -> None:
    """Test deleting a script."""
    with patch.object(config, "SECTIONS", [script]):
        await async_setup_component(hass, "config", {})

    assert sorted(hass.states.async_entity_ids("script")) == [
        "script.one",
        "script.two",
    ]

    assert len(entity_registry.entities) == 2

    client = await hass_client()

    orig_data = {"one": {}, "two": {}}
    hass_config_store["scripts.yaml"] = orig_data

    resp = await client.delete("/api/config/script/config/two")
    await hass.async_block_till_done()

    assert sorted(hass.states.async_entity_ids("script")) == [
        "script.one",
    ]

    assert resp.status == HTTPStatus.OK
    result = await resp.json()
    assert result == {"result": "ok"}

    assert hass_config_store["scripts.yaml"] == {"one": {}}

    assert len(entity_registry.entities) == 1