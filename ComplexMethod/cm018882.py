async def test_upload_view(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    temp_dir: str,
    tmp_path: Path,
    hass_admin_user: MockUser,
) -> None:
    """Allow uploading media."""
    # We need a temp dir that's not under tempdir fixture
    extra_media_dir = tmp_path
    hass.config.media_dirs["another_path"] = temp_dir

    img = (Path(__file__).parent.parent / "image_upload/logo.png").read_bytes()

    def get_file(name):
        pic = io.BytesIO(img)
        pic.name = name
        return pic

    client = await hass_client()

    # Test normal upload
    with patch.object(Path, "mkdir", autospec=True, return_value=None) as mock_mkdir:
        res = await client.post(
            "/api/media_source/local_source/upload",
            data={
                "media_content_id": "media-source://media_source/test_dir",
                "file": get_file("logo.png"),
            },
        )

    assert res.status == 200
    data = await res.json()
    assert data["media_content_id"] == "media-source://media_source/test_dir/logo.png"
    uploaded_path = Path(temp_dir) / "logo.png"
    assert uploaded_path.is_file()
    mock_mkdir.assert_called_once()

    resolved = await media_source.async_resolve_media(
        hass, data["media_content_id"], target_media_player=None
    )
    assert resolved.url == "/media/test_dir/logo.png"
    assert resolved.mime_type == "image/png"
    assert resolved.path == uploaded_path

    # Test with bad media source ID
    for bad_id in (
        # Main dir doesn't exist
        "media-source://media_source/test_dir2",
        # Location is invalid
        "media-source://media_source/test_dir/..",
        # Domain != media_source
        "media-source://nest/test_dir/.",
        # Other directory
        f"media-source://media_source/another_path///{extra_media_dir}/",
        # Completely something else
        "http://bla",
    ):
        res = await client.post(
            "/api/media_source/local_source/upload",
            data={
                "media_content_id": bad_id,
                "file": get_file("bad-source-id.png"),
            },
        )

        assert res.status == 400, bad_id
        assert not (Path(temp_dir) / "bad-source-id.png").is_file()

    # Test invalid POST data
    res = await client.post(
        "/api/media_source/local_source/upload",
        data={
            "media_content_id": "media-source://media_source/test_dir/.",
            "file": get_file("invalid-data.png"),
            "incorrect": "format",
        },
    )

    assert res.status == 400
    assert not (Path(temp_dir) / "invalid-data.png").is_file()

    # Test invalid content type
    text_file = io.BytesIO(b"Hello world")
    text_file.name = "hello.txt"
    res = await client.post(
        "/api/media_source/local_source/upload",
        data={
            "media_content_id": "media-source://media_source/test_dir/.",
            "file": text_file,
        },
    )

    assert res.status == 400
    assert not (Path(temp_dir) / "hello.txt").is_file()

    # Test invalid filename
    with patch(
        "aiohttp.formdata.guess_filename", return_value="../invalid-filename.png"
    ):
        res = await client.post(
            "/api/media_source/local_source/upload",
            data={
                "media_content_id": "media-source://media_source/test_dir/.",
                "file": get_file("../invalid-filename.png"),
            },
        )

    assert res.status == 400
    assert not (Path(temp_dir) / "../invalid-filename.png").is_file()

    # Remove admin access
    hass_admin_user.groups = []
    res = await client.post(
        "/api/media_source/local_source/upload",
        data={
            "media_content_id": "media-source://media_source/test_dir/.",
            "file": get_file("no-admin-test.png"),
        },
    )

    assert res.status == 401
    assert not (Path(temp_dir) / "no-admin-test.png").is_file()