async def test_webhook_enable_encryption(
    hass: HomeAssistant,
    create_registrations: tuple[dict[str, Any], dict[str, Any]],
    webhook_client: TestClient,
) -> None:
    """Test that encryption can be added to a reg initially created without."""
    webhook_id = create_registrations[1]["webhook_id"]

    enable_enc_resp = await webhook_client.post(
        f"/api/webhook/{webhook_id}",
        json={"type": "enable_encryption"},
    )

    assert enable_enc_resp.status == HTTPStatus.OK

    enable_enc_json = await enable_enc_resp.json()
    assert len(enable_enc_json) == 1
    assert CONF_SECRET in enable_enc_json

    key = enable_enc_json["secret"]

    enc_required_resp = await webhook_client.post(
        f"/api/webhook/{webhook_id}",
        json=RENDER_TEMPLATE,
    )

    assert enc_required_resp.status == HTTPStatus.BAD_REQUEST

    enc_required_json = await enc_required_resp.json()
    assert "error" in enc_required_json
    assert enc_required_json["success"] is False
    assert enc_required_json["error"]["code"] == "encryption_required"

    enc_data = encrypt_payload(key, RENDER_TEMPLATE["data"])

    container = {
        "type": "render_template",
        "encrypted": True,
        "encrypted_data": enc_data,
    }

    enc_resp = await webhook_client.post(f"/api/webhook/{webhook_id}", json=container)

    assert enc_resp.status == HTTPStatus.OK

    enc_json = await enc_resp.json()
    assert "encrypted_data" in enc_json

    decrypted_data = decrypt_payload(key, enc_json["encrypted_data"])

    assert decrypted_data == {"one": "Hello world"}