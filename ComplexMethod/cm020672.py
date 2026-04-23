async def test_add_group_member(hass: HomeAssistant, zha_client) -> None:
    """Test adding a ZHA zigbee group member."""
    await zha_client.send_json(
        {
            ID: 12,
            TYPE: "zha/group/add",
            GROUP_NAME: "new_group",
        }
    )

    msg = await zha_client.receive_json()
    assert msg["id"] == 12
    assert msg["type"] == TYPE_RESULT

    added_group = msg["result"]

    assert len(added_group["members"]) == 0

    await zha_client.send_json(
        {
            ID: 13,
            TYPE: "zha/group/members/add",
            GROUP_ID: added_group["group_id"],
            "members": [{"ieee": IEEE_GROUPABLE_DEVICE, "endpoint_id": 1}],
        }
    )

    msg = await zha_client.receive_json()
    assert msg["id"] == 13
    assert msg["type"] == TYPE_RESULT

    added_group = msg["result"]

    assert len(added_group["members"]) == 1
    assert added_group["name"] == "new_group"
    assert added_group["members"][0]["device"]["ieee"] == IEEE_GROUPABLE_DEVICE