async def test_add_group(hass: HomeAssistant, zha_client) -> None:
    """Test adding and getting a new ZHA zigbee group."""
    await zha_client.send_json(
        {
            ID: 12,
            TYPE: "zha/group/add",
            GROUP_NAME: "new_group",
            "members": [{"ieee": IEEE_GROUPABLE_DEVICE, "endpoint_id": 1}],
        }
    )

    msg = await zha_client.receive_json()
    assert msg["id"] == 12
    assert msg["type"] == TYPE_RESULT

    added_group = msg["result"]

    groupable_device = get_zha_gateway_proxy(hass).device_proxies[
        EUI64.convert(IEEE_GROUPABLE_DEVICE)
    ]

    assert added_group["name"] == "new_group"
    assert len(added_group["members"]) == 1
    assert added_group["members"][0]["device"]["ieee"] == IEEE_GROUPABLE_DEVICE
    assert (
        added_group["members"][0]["device"]["device_reg_id"]
        == groupable_device.device_id
    )

    await zha_client.send_json({ID: 13, TYPE: "zha/groups"})

    msg = await zha_client.receive_json()
    assert msg["id"] == 13
    assert msg["type"] == TYPE_RESULT

    groups = msg["result"]
    assert len(groups) == 2

    for group in groups:
        assert group["name"] == FIXTURE_GRP_NAME or group["name"] == "new_group"