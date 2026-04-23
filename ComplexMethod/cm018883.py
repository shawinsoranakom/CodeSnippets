async def test_remove_file(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    temp_dir: str,
    hass_admin_user: MockUser,
) -> None:
    """Allow uploading media."""

    msg_count = 0
    file_count = 0

    def msgid():
        nonlocal msg_count
        msg_count += 1
        return msg_count

    def create_file():
        nonlocal file_count
        file_count += 1
        to_delete_path = Path(temp_dir) / f"to_delete_{file_count}.txt"
        to_delete_path.touch()
        return to_delete_path

    client = await hass_ws_client(hass)
    to_delete = create_file()

    await client.send_json(
        {
            "id": msgid(),
            "type": "media_source/local_source/remove",
            "media_content_id": f"media-source://media_source/test_dir/{to_delete.name}",
        }
    )

    msg = await client.receive_json()

    assert msg["success"]

    assert not to_delete.exists()

    # Test with bad media source ID
    extra_id_file = create_file()
    for bad_id, err in (
        # Not exists
        (
            "media-source://media_source/test_dir/not_exist.txt",
            websocket_api.ERR_NOT_FOUND,
        ),
        # Only a dir
        ("media-source://media_source/test_dir", websocket_api.ERR_NOT_SUPPORTED),
        # File with extra identifiers
        (
            f"media-source://media_source/test_dir/bla/../{extra_id_file.name}",
            websocket_api.ERR_INVALID_FORMAT,
        ),
        # Location is invalid
        ("media-source://media_source/test_dir/..", websocket_api.ERR_INVALID_FORMAT),
        # Domain != media_source
        ("media-source://nest/test_dir/.", websocket_api.ERR_INVALID_FORMAT),
        # Completely something else
        ("http://bla", websocket_api.ERR_INVALID_FORMAT),
    ):
        await client.send_json(
            {
                "id": msgid(),
                "type": "media_source/local_source/remove",
                "media_content_id": bad_id,
            }
        )

        msg = await client.receive_json()

        assert not msg["success"], bad_id
        assert msg["error"]["code"] == err

    assert extra_id_file.exists()

    # Test error deleting
    to_delete_2 = create_file()

    with patch("pathlib.Path.unlink", side_effect=OSError):
        await client.send_json(
            {
                "id": msgid(),
                "type": "media_source/local_source/remove",
                "media_content_id": f"media-source://media_source/test_dir/{to_delete_2.name}",
            }
        )

        msg = await client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == websocket_api.ERR_UNKNOWN_ERROR

    # Test requires admin access
    to_delete_3 = create_file()
    hass_admin_user.groups = []

    await client.send_json(
        {
            "id": msgid(),
            "type": "media_source/local_source/remove",
            "media_content_id": f"media-source://media_source/test_dir/{to_delete_3.name}",
        }
    )

    msg = await client.receive_json()

    assert not msg["success"]
    assert to_delete_3.is_file()