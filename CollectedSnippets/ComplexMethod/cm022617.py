async def test_event_media_data(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    hass_client_no_auth: ClientSessionGenerator,
) -> None:
    """Test an event with a file path generates media data."""
    await async_setup_component(hass, "http", {"http": {}})

    client = create_mock_motioneye_client()
    config_entry = await setup_mock_motioneye_config_entry(hass, client=client)

    device = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={TEST_CAMERA_DEVICE_IDENTIFIER},
    )

    hass_client = await hass_client_no_auth()

    events = async_capture_events(hass, f"{DOMAIN}.{EVENT_FILE_STORED}")

    client.get_movie_url = Mock(return_value="http://movie-url")
    client.get_image_url = Mock(return_value="http://image-url")

    # Test: Movie storage.
    client.is_file_type_image = Mock(return_value=False)
    resp = await hass_client.post(
        URL_WEBHOOK_PATH.format(webhook_id=config_entry.data[CONF_WEBHOOK_ID]),
        json={
            ATTR_DEVICE_ID: device.id,
            ATTR_EVENT_TYPE: EVENT_FILE_STORED,
            "file_path": f"/var/lib/motioneye/{TEST_CAMERA_NAME}/dir/one",
            "file_type": "8",
        },
    )
    assert resp.status == HTTPStatus.OK
    assert len(events) == 1
    assert events[-1].data["file_url"] == "http://movie-url"
    assert (
        events[-1].data["media_content_id"]
        == f"media-source://motioneye/{TEST_CONFIG_ENTRY_ID}#{device.id}#movies#/dir/one"
    )
    assert client.get_movie_url.call_args == call(TEST_CAMERA_ID, "/dir/one")

    # Test: Image storage.
    client.is_file_type_image = Mock(return_value=True)
    resp = await hass_client.post(
        URL_WEBHOOK_PATH.format(webhook_id=config_entry.data[CONF_WEBHOOK_ID]),
        json={
            ATTR_DEVICE_ID: device.id,
            ATTR_EVENT_TYPE: EVENT_FILE_STORED,
            "file_path": f"/var/lib/motioneye/{TEST_CAMERA_NAME}/dir/two",
            "file_type": "4",
        },
    )
    assert resp.status == HTTPStatus.OK
    assert len(events) == 2
    assert events[-1].data["file_url"] == "http://image-url"
    assert (
        events[-1].data["media_content_id"]
        == f"media-source://motioneye/{TEST_CONFIG_ENTRY_ID}#{device.id}#images#/dir/two"
    )
    assert client.get_image_url.call_args == call(TEST_CAMERA_ID, "/dir/two")

    # Test: Invalid file type.
    resp = await hass_client.post(
        URL_WEBHOOK_PATH.format(webhook_id=config_entry.data[CONF_WEBHOOK_ID]),
        json={
            ATTR_DEVICE_ID: device.id,
            ATTR_EVENT_TYPE: EVENT_FILE_STORED,
            "file_path": f"/var/lib/motioneye/{TEST_CAMERA_NAME}/dir/three",
            "file_type": "NOT_AN_INT",
        },
    )
    assert resp.status == HTTPStatus.OK
    assert len(events) == 3
    assert "file_url" not in events[-1].data
    assert "media_content_id" not in events[-1].data

    # Test: Different file path.
    resp = await hass_client.post(
        URL_WEBHOOK_PATH.format(webhook_id=config_entry.data[CONF_WEBHOOK_ID]),
        json={
            ATTR_DEVICE_ID: device.id,
            ATTR_EVENT_TYPE: EVENT_FILE_STORED,
            "file_path": "/var/random",
            "file_type": "8",
        },
    )
    assert resp.status == HTTPStatus.OK
    assert len(events) == 4
    assert "file_url" not in events[-1].data
    assert "media_content_id" not in events[-1].data

    # Test: Not a loaded motionEye config entry.
    other_config_entry = MockConfigEntry()
    other_config_entry.add_to_hass(hass)
    wrong_device = device_registry.async_get_or_create(
        config_entry_id=other_config_entry.entry_id, identifiers={("motioneye", "a_1")}
    )
    resp = await hass_client.post(
        URL_WEBHOOK_PATH.format(webhook_id=config_entry.data[CONF_WEBHOOK_ID]),
        json={
            ATTR_DEVICE_ID: wrong_device.id,
            ATTR_EVENT_TYPE: EVENT_FILE_STORED,
            "file_path": "/var/random",
            "file_type": "8",
        },
    )
    assert resp.status == HTTPStatus.OK
    assert len(events) == 5
    assert "file_url" not in events[-1].data
    assert "media_content_id" not in events[-1].data

    # Test: No root directory.
    camera = copy.deepcopy(TEST_CAMERA)
    del camera[KEY_ROOT_DIRECTORY]
    client.async_get_cameras = AsyncMock(return_value={"cameras": [camera]})
    async_fire_time_changed(hass, dt_util.utcnow() + DEFAULT_SCAN_INTERVAL)
    await hass.async_block_till_done()

    resp = await hass_client.post(
        URL_WEBHOOK_PATH.format(webhook_id=config_entry.data[CONF_WEBHOOK_ID]),
        json={
            ATTR_DEVICE_ID: device.id,
            ATTR_EVENT_TYPE: EVENT_FILE_STORED,
            "file_path": f"/var/lib/motioneye/{TEST_CAMERA_NAME}/dir/four",
            "file_type": "8",
        },
    )
    assert resp.status == HTTPStatus.OK
    assert len(events) == 6
    assert "file_url" not in events[-1].data
    assert "media_content_id" not in events[-1].data

    # Test: Device has incorrect device identifiers.
    device_registry.async_update_device(
        device_id=device.id, new_identifiers={("not", "motioneye")}
    )
    resp = await hass_client.post(
        URL_WEBHOOK_PATH.format(webhook_id=config_entry.data[CONF_WEBHOOK_ID]),
        json={
            ATTR_DEVICE_ID: device.id,
            ATTR_EVENT_TYPE: EVENT_FILE_STORED,
            "file_path": f"/var/lib/motioneye/{TEST_CAMERA_NAME}/dir/five",
            "file_type": "8",
        },
    )
    assert resp.status == HTTPStatus.OK
    assert len(events) == 7
    assert "file_url" not in events[-1].data
    assert "media_content_id" not in events[-1].data