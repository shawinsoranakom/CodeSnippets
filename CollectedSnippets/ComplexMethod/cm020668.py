async def test_list_groups(zha_client) -> None:
    """Test getting ZHA zigbee groups."""
    await zha_client.send_json({ID: 7, TYPE: "zha/groups"})

    msg = await zha_client.receive_json()
    assert msg["id"] == 7
    assert msg["type"] == TYPE_RESULT

    groups = msg["result"]
    assert len(groups) == 1

    for group in groups:
        assert group["group_id"] == FIXTURE_GRP_ID
        assert group["name"] == FIXTURE_GRP_NAME
        assert group["members"] == []