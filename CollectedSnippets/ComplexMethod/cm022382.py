async def test_delete_scene(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    entity_registry: er.EntityRegistry,
    hass_config_store: dict[str, Any],
) -> None:
    """Test deleting a scene."""

    assert len(entity_registry.entities) == 2

    with patch.object(config, "SECTIONS", [scene]):
        assert await async_setup_component(hass, "config", {})

    assert sorted(hass.states.async_entity_ids("scene")) == [
        "scene.light_off",
        "scene.light_on",
    ]

    client = await hass_client()

    orig_data = [{"id": "light_on"}, {"id": "light_off"}]
    hass_config_store["scenes.yaml"] = orig_data

    resp = await client.delete("/api/config/scene/config/light_on")
    await hass.async_block_till_done()

    assert sorted(hass.states.async_entity_ids("scene")) == [
        "scene.light_off",
    ]

    assert resp.status == HTTPStatus.OK
    result = await resp.json()
    assert result == {"result": "ok"}

    assert hass_config_store["scenes.yaml"] == [
        {"id": "light_off"},
    ]

    assert len(entity_registry.entities) == 1