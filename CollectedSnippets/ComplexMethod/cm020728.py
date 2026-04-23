async def async_set_user_code(hass: HomeAssistant, cluster: Cluster, entity_id: str):
    """Test set lock code functionality from hass."""
    with patch("zigpy.zcl.Cluster.request", return_value=[zcl_f.Status.SUCCESS]):
        # set lock code via service call
        await hass.services.async_call(
            "zha",
            "set_lock_user_code",
            {"entity_id": entity_id, "code_slot": 3, "user_code": "13246579"},
            blocking=True,
        )
        assert cluster.request.call_count == 1
        assert cluster.request.call_args[0][0] is False
        assert (
            cluster.request.call_args[0][1]
            == closures.DoorLock.ServerCommandDefs.set_pin_code.id
        )
        assert cluster.request.call_args[0][3] == 2  # user slot 3 => internal slot 2
        assert cluster.request.call_args[0][4] == closures.DoorLock.UserStatus.Enabled
        assert (
            cluster.request.call_args[0][5] == closures.DoorLock.UserType.Unrestricted
        )
        assert cluster.request.call_args[0][6] == "13246579"