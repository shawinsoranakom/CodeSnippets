async def test_get_lock_users_with_nullvalue_credentials(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test get_lock_users handles NullValue credentials from Matter SDK."""
    matter_client.send_device_command = AsyncMock(
        side_effect=[
            {
                "userIndex": 1,
                "userStatus": 1,
                "userName": "User No Creds",
                "userUniqueID": 100,
                "userType": 0,
                "credentialRule": 0,
                "credentials": NullValue,
                "nextUserIndex": None,
            },
        ]
    )

    result = await hass.services.async_call(
        DOMAIN,
        "get_lock_users",
        {ATTR_ENTITY_ID: "lock.mock_door_lock"},
        blocking=True,
        return_response=True,
    )

    assert matter_client.send_device_command.call_count == 1
    assert matter_client.send_device_command.call_args == call(
        node_id=matter_node.node_id,
        endpoint_id=1,
        command=clusters.DoorLock.Commands.GetUser(userIndex=1),
    )

    lock_users = result["lock.mock_door_lock"]
    assert len(lock_users["users"]) == 1
    user = lock_users["users"][0]
    assert user["user_index"] == 1
    assert user["user_name"] == "User No Creds"
    assert user["user_unique_id"] == 100
    assert user["credentials"] == []