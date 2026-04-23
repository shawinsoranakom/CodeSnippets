async def test_ws_permit_with_qr_code(
    app_controller: ControllerApplication, zha_client, params, src_ieee, code
) -> None:
    """Test permit service with install code from qr code."""

    await zha_client.send_json(
        {ID: 14, TYPE: f"{DOMAIN}/devices/{SERVICE_PERMIT}", **params}
    )

    msg_type = None
    while msg_type != TYPE_RESULT:
        # There will be logging events coming over the websocket
        # as well so we want to ignore those
        msg = await zha_client.receive_json()
        msg_type = msg["type"]

    assert msg["id"] == 14
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]

    assert app_controller.permit.await_count == 0
    assert app_controller.permit_with_link_key.call_count == 1
    assert app_controller.permit_with_link_key.await_args[1]["time_s"] == 60
    assert app_controller.permit_with_link_key.await_args[1]["node"] == src_ieee
    assert app_controller.permit_with_link_key.await_args[1]["link_key"] == code