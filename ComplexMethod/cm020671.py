async def test_remove_group(zha_client) -> None:
    """Test removing a new ZHA zigbee group."""

    await zha_client.send_json({ID: 14, TYPE: "zha/groups"})

    msg = await zha_client.receive_json()
    assert msg["id"] == 14
    assert msg["type"] == TYPE_RESULT

    groups = msg["result"]
    assert len(groups) == 1

    await zha_client.send_json(
        {ID: 15, TYPE: "zha/group/remove", GROUP_IDS: [FIXTURE_GRP_ID]}
    )

    msg = await zha_client.receive_json()
    assert msg["id"] == 15
    assert msg["type"] == TYPE_RESULT

    groups_remaining = msg["result"]
    assert len(groups_remaining) == 0

    await zha_client.send_json({ID: 16, TYPE: "zha/groups"})

    msg = await zha_client.receive_json()
    assert msg["id"] == 16
    assert msg["type"] == TYPE_RESULT

    groups = msg["result"]
    assert len(groups) == 0