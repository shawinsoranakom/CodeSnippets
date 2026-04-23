async def test_list_groupable_devices(
    hass: HomeAssistant, zha_client, zigpy_app_controller
) -> None:
    """Test getting ZHA devices that have a group cluster."""
    # Ensure the coordinator doesn't have a group cluster
    coordinator = zigpy_app_controller.get_device(nwk=0x0000)

    del coordinator.endpoints[1].in_clusters[Groups.cluster_id]

    await zha_client.send_json({ID: 10, TYPE: "zha/devices/groupable"})

    msg = await zha_client.receive_json()
    assert msg["id"] == 10
    assert msg["type"] == TYPE_RESULT

    device_endpoints = msg["result"]
    assert len(device_endpoints) == 1

    for endpoint in device_endpoints:
        assert endpoint["device"][ATTR_IEEE] == "01:2d:6f:00:0a:90:69:e8"
        assert endpoint["device"][ATTR_MANUFACTURER] is not None
        assert endpoint["device"][ATTR_MODEL] is not None
        assert endpoint["device"][ATTR_NAME] is not None
        assert endpoint["device"][ATTR_QUIRK_APPLIED] is not None
        assert endpoint["device"]["entities"] is not None
        assert endpoint["endpoint_id"] is not None
        assert endpoint["entities"] is not None

        for entity_reference in endpoint["device"]["entities"]:
            assert entity_reference[ATTR_NAME] is not None
            assert entity_reference["entity_id"] is not None

        if len(endpoint["entities"]) == 1:
            assert endpoint["entities"][0]["original_name"] is None
        else:
            for entity_reference in endpoint["entities"]:
                assert entity_reference["original_name"] is not None

    # Make sure there are no groupable devices when the device is unavailable
    # Make device unavailable
    get_zha_gateway_proxy(hass).device_proxies[
        EUI64.convert(IEEE_GROUPABLE_DEVICE)
    ].device.available = False
    await hass.async_block_till_done(wait_background_tasks=True)

    await zha_client.send_json({ID: 11, TYPE: "zha/devices/groupable"})

    msg = await zha_client.receive_json()
    assert msg["id"] == 11
    assert msg["type"] == TYPE_RESULT

    device_endpoints = msg["result"]
    assert len(device_endpoints) == 0