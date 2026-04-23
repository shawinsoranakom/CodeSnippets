async def test_device_clusters(hass: HomeAssistant, zha_client) -> None:
    """Test getting device cluster info."""
    await zha_client.send_json(
        {ID: 5, TYPE: "zha/devices/clusters", ATTR_IEEE: IEEE_SWITCH_DEVICE}
    )

    msg = await zha_client.receive_json()

    assert len(msg["result"]) == 2

    cluster_infos = sorted(msg["result"], key=lambda k: k[ID])

    cluster_info = cluster_infos[0]
    assert cluster_info[TYPE] == CLUSTER_TYPE_IN
    assert cluster_info[ID] == 0
    assert cluster_info[ATTR_NAME] == "Basic"

    cluster_info = cluster_infos[1]
    assert cluster_info[TYPE] == CLUSTER_TYPE_IN
    assert cluster_info[ID] == 6
    assert cluster_info[ATTR_NAME] == "OnOff"