async def test_sync_request(
    hass_fixture, assistant_client, auth_header, entity_registry: er.EntityRegistry
) -> None:
    """Test a sync request."""
    entity_entry1 = entity_registry.async_get_or_create(
        "switch",
        "test",
        "switch_config_id",
        suggested_object_id="config_switch",
        entity_category=EntityCategory.CONFIG,
    )
    entity_entry2 = entity_registry.async_get_or_create(
        "switch",
        "test",
        "switch_diagnostic_id",
        suggested_object_id="diagnostic_switch",
        entity_category=EntityCategory.DIAGNOSTIC,
    )
    entity_entry3 = entity_registry.async_get_or_create(
        "switch",
        "test",
        "switch_hidden_integration_id",
        suggested_object_id="hidden_integration_switch",
        hidden_by=er.RegistryEntryHider.INTEGRATION,
    )
    entity_entry4 = entity_registry.async_get_or_create(
        "switch",
        "test",
        "switch_hidden_user_id",
        suggested_object_id="hidden_user_switch",
        hidden_by=er.RegistryEntryHider.USER,
    )

    # These should not show up in the sync request
    hass_fixture.states.async_set(entity_entry1.entity_id, "on")
    hass_fixture.states.async_set(entity_entry2.entity_id, "something_else")
    hass_fixture.states.async_set(entity_entry3.entity_id, "blah")
    hass_fixture.states.async_set(entity_entry4.entity_id, "foo")

    reqid = "5711642932632160983"
    data = {"requestId": reqid, "inputs": [{"intent": "action.devices.SYNC"}]}
    result = await assistant_client.post(
        ga.const.GOOGLE_ASSISTANT_API_ENDPOINT,
        data=json.dumps(data),
        headers=auth_header,
    )
    assert result.status == HTTPStatus.OK
    body = await result.json()
    assert body.get("requestId") == reqid
    devices = body["payload"]["devices"]
    assert sorted(dev["id"] for dev in devices) == sorted(
        dev["id"] for dev in DEMO_DEVICES
    )

    for dev in devices:
        assert dev["id"] not in CLOUD_NEVER_EXPOSED_ENTITIES

    for dev, demo in zip(
        sorted(devices, key=lambda d: d["id"]),
        sorted(DEMO_DEVICES, key=lambda d: d["id"]),
        strict=False,
    ):
        assert dev["name"] == demo["name"]
        assert set(dev["traits"]) == set(demo["traits"])
        assert dev["type"] == demo["type"]