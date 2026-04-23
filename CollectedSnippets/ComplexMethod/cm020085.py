async def test_delete_entity_error(
    hass: HomeAssistant,
    knx: KNXTestKit,
    entity_registry: er.EntityRegistry,
    hass_ws_client: WebSocketGenerator,
    hass_storage: dict[str, Any],
) -> None:
    """Test unsuccessful entity deletion."""
    await knx.setup_integration()
    client = await hass_ws_client(hass)

    # delete unknown entity
    await client.send_json_auto_id(
        {
            "type": "knx/delete_entity",
            "entity_id": "switch.non_existing_entity",
        }
    )
    res = await client.receive_json()
    assert not res["success"], res
    assert res["error"]["code"] == "home_assistant_error"
    assert res["error"]["message"].startswith("Entity not found")

    # delete entity not in config store
    test_entity_id = "sensor.knx_interface_individual_address"
    assert entity_registry.async_get(test_entity_id)
    await client.send_json_auto_id(
        {
            "type": "knx/delete_entity",
            "entity_id": test_entity_id,
        }
    )
    res = await client.receive_json()
    assert not res["success"], res
    assert res["error"]["code"] == "home_assistant_error"
    assert res["error"]["message"].startswith("Entity not found")