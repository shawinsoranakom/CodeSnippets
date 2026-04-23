async def test_webhook_handle_decryption_fail(
    create_registrations: tuple[dict[str, Any], dict[str, Any]],
    webhook_client: TestClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that we can encrypt/decrypt properly."""
    key = create_registrations[0]["secret"]

    # Send valid data
    data = encrypt_payload(key, RENDER_TEMPLATE["data"])
    container = {"type": "render_template", "encrypted": True, "encrypted_data": data}
    resp = await webhook_client.post(
        f"/api/webhook/{create_registrations[0]['webhook_id']}", json=container
    )

    assert resp.status == HTTPStatus.OK
    webhook_json = await resp.json()
    decrypted_data = decrypt_payload(key, webhook_json["encrypted_data"])
    assert decrypted_data == {"one": "Hello world"}
    caplog.clear()

    # Send invalid JSON data
    data = encrypt_payload(key, "{not_valid", encode_json=False)
    container = {"type": "render_template", "encrypted": True, "encrypted_data": data}
    resp = await webhook_client.post(
        f"/api/webhook/{create_registrations[0]['webhook_id']}", json=container
    )

    assert resp.status == HTTPStatus.OK
    assert await resp.json() == {}
    assert "Ignoring invalid JSON in encrypted payload" in caplog.text
    caplog.clear()

    # Break the key, and send JSON data
    data = encrypt_payload(key[::-1], RENDER_TEMPLATE["data"])
    container = {"type": "render_template", "encrypted": True, "encrypted_data": data}
    resp = await webhook_client.post(
        f"/api/webhook/{create_registrations[0]['webhook_id']}", json=container
    )

    assert resp.status == HTTPStatus.OK
    assert await resp.json() == {}
    assert "Ignoring encrypted payload because unable to decrypt" in caplog.text