async def test_webhook_handle_decryption_legacy_upgrade(
    create_registrations: tuple[dict[str, Any], dict[str, Any]],
    webhook_client: TestClient,
) -> None:
    """Test that we can encrypt/decrypt properly."""
    key = create_registrations[0]["secret"]

    # Send using legacy method
    data = encrypt_payload_legacy(key, RENDER_TEMPLATE["data"])

    container = {"type": "render_template", "encrypted": True, "encrypted_data": data}

    resp = await webhook_client.post(
        f"/api/webhook/{create_registrations[0]['webhook_id']}", json=container
    )

    assert resp.status == HTTPStatus.OK

    webhook_json = await resp.json()
    assert "encrypted_data" in webhook_json

    decrypted_data = decrypt_payload_legacy(key, webhook_json["encrypted_data"])

    assert decrypted_data == {"one": "Hello world"}

    # Send using new method
    data = encrypt_payload(key, RENDER_TEMPLATE["data"])

    container = {"type": "render_template", "encrypted": True, "encrypted_data": data}

    resp = await webhook_client.post(
        f"/api/webhook/{create_registrations[0]['webhook_id']}", json=container
    )

    assert resp.status == HTTPStatus.OK

    webhook_json = await resp.json()
    assert "encrypted_data" in webhook_json

    decrypted_data = decrypt_payload(key, webhook_json["encrypted_data"])

    assert decrypted_data == {"one": "Hello world"}

    # Send using legacy method - no longer possible
    data = encrypt_payload_legacy(key, RENDER_TEMPLATE["data"])

    container = {"type": "render_template", "encrypted": True, "encrypted_data": data}

    resp = await webhook_client.post(
        f"/api/webhook/{create_registrations[0]['webhook_id']}", json=container
    )

    assert resp.status == HTTPStatus.OK
    assert await resp.json() == {}