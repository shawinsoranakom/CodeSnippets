async def test_script_service_changed_entity_id(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test the script service works for scripts with overridden entity_id."""
    entry = entity_registry.async_get_or_create("script", "script", "test")
    entry = entity_registry.async_update_entity(
        entry.entity_id, new_entity_id="script.custom_entity_id"
    )
    assert entry.entity_id == "script.custom_entity_id"

    calls = []

    @callback
    def record_call(service):
        """Add recorded event to set."""
        calls.append(service)

    hass.services.async_register("test", "script", record_call)

    # Make sure the service of a script with overridden entity_id works
    assert await async_setup_component(
        hass,
        "script",
        {
            "script": {
                "test": {
                    "sequence": {
                        "action": "test.script",
                        "data_template": {"entity_id": "{{ this.entity_id }}"},
                    }
                }
            }
        },
    )

    await hass.services.async_call(DOMAIN, "test", {"greeting": "world"})

    await hass.async_block_till_done()

    assert len(calls) == 1
    assert calls[0].data["entity_id"] == "script.custom_entity_id"

    # Change entity while the script entity is loaded, and make sure the service still works
    entry = entity_registry.async_update_entity(
        entry.entity_id, new_entity_id="script.custom_entity_id_2"
    )
    assert entry.entity_id == "script.custom_entity_id_2"
    await hass.async_block_till_done()

    await hass.services.async_call(DOMAIN, "test", {"greeting": "world"})
    await hass.async_block_till_done()

    assert len(calls) == 2
    assert calls[1].data["entity_id"] == "script.custom_entity_id_2"