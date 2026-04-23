async def test_unauthorized_view(hass: HomeAssistant, hue_client) -> None:
    """Test unauthorized view."""
    await setup_hue(hass)
    client = await hue_client()
    request_json = {"devicetype": "my_device"}

    result = await client.get(
        "/api/unauthorized", data=json.dumps(request_json), timeout=5
    )

    assert result.status == HTTPStatus.OK
    assert CONTENT_TYPE_JSON in result.headers["content-type"]

    resp_json = await result.json()
    assert len(resp_json) == 1
    success_json = resp_json[0]
    assert len(success_json) == 1

    assert "error" in success_json
    error_json = success_json["error"]
    assert len(error_json) == 3
    assert "/" in error_json["address"]
    assert "unauthorized user" in error_json["description"]
    assert "1" in error_json["type"]