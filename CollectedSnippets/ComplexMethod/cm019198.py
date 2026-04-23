async def test_browsing(
    hass: HomeAssistant,
    reolink_host: MagicMock,
    config_entry: MockConfigEntry,
    device_registry: dr.DeviceRegistry,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test browsing the Reolink three."""
    entry_id = config_entry.entry_id
    reolink_host.supported.return_value = 1
    reolink_host.model = "Reolink TrackMix PoE"
    reolink_host.is_nvr = False

    with patch("homeassistant.components.reolink.PLATFORMS", [Platform.CAMERA]):
        assert await hass.config_entries.async_setup(entry_id) is True
    await hass.async_block_till_done()

    entries = dr.async_entries_for_config_entry(device_registry, entry_id)
    assert len(entries) > 0
    device_registry.async_update_device(entries[0].id, name_by_user=TEST_CAM_NAME)

    caplog.set_level(logging.DEBUG)

    # browse root
    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}")

    browse_root_id = f"CAM|{entry_id}|{TEST_CHANNEL}"
    assert browse.domain == DOMAIN
    assert browse.title == "Reolink"
    assert browse.identifier is None
    assert browse.children[0].identifier == browse_root_id
    assert browse.children[0].title == f"{TEST_CAM_NAME} lens 0"

    # browse resolution select
    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}/{browse_root_id}")

    browse_resolution_id = f"RESs|{entry_id}|{TEST_CHANNEL}"
    browse_res_sub_id = f"RES|{entry_id}|{TEST_CHANNEL}|sub"
    browse_res_main_id = f"RES|{entry_id}|{TEST_CHANNEL}|main"
    browse_res_AT_sub_id = f"RES|{entry_id}|{TEST_CHANNEL}|autotrack_sub"
    browse_res_AT_main_id = f"RES|{entry_id}|{TEST_CHANNEL}|autotrack_main"
    assert browse.domain == DOMAIN
    assert browse.title == f"{TEST_CAM_NAME} lens 0"
    assert browse.identifier == browse_resolution_id
    assert browse.children[0].identifier == browse_res_sub_id
    assert browse.children[1].identifier == browse_res_main_id
    assert browse.children[2].identifier == browse_res_AT_sub_id
    assert browse.children[3].identifier == browse_res_AT_main_id

    # browse camera recording days
    mock_status = MagicMock()
    mock_status.year = TEST_YEAR
    mock_status.month = TEST_MONTH
    mock_status.days = (TEST_DAY, TEST_DAY2)
    reolink_host.request_vod_files.return_value = ([mock_status], [])

    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}/{browse_res_sub_id}")
    assert browse.domain == DOMAIN
    assert browse.title == f"{TEST_CAM_NAME} lens 0 Low res."

    browse = await async_browse_media(
        hass, f"{URI_SCHEME}{DOMAIN}/{browse_res_AT_sub_id}"
    )
    assert browse.domain == DOMAIN
    assert browse.title == f"{TEST_CAM_NAME} lens 0 Telephoto low res."

    browse = await async_browse_media(
        hass, f"{URI_SCHEME}{DOMAIN}/{browse_res_AT_main_id}"
    )
    assert browse.domain == DOMAIN
    assert browse.title == f"{TEST_CAM_NAME} lens 0 Telephoto high res."

    browse = await async_browse_media(
        hass, f"{URI_SCHEME}{DOMAIN}/{browse_res_main_id}"
    )

    browse_days_id = f"DAYS|{entry_id}|{TEST_CHANNEL}|{TEST_STREAM}"
    browse_day_0_id = f"DAY|{entry_id}|{TEST_CHANNEL}|{TEST_STREAM}|{TEST_YEAR}|{TEST_MONTH}|{TEST_DAY}"
    browse_day_1_id = f"DAY|{entry_id}|{TEST_CHANNEL}|{TEST_STREAM}|{TEST_YEAR}|{TEST_MONTH}|{TEST_DAY2}"
    assert browse.domain == DOMAIN
    assert browse.title == f"{TEST_CAM_NAME} lens 0 High res."
    assert browse.identifier == browse_days_id
    assert browse.children[0].identifier == browse_day_0_id
    assert browse.children[1].identifier == browse_day_1_id

    # browse camera recording files on day
    mock_vod_file = MagicMock()
    mock_vod_file.start_time = TEST_START_TIME
    mock_vod_file.start_time_id = TEST_START
    mock_vod_file.end_time_id = TEST_END
    mock_vod_file.duration = timedelta(minutes=5)
    mock_vod_file.file_name = TEST_FILE_NAME
    mock_vod_file.triggers = VOD_trigger.PERSON
    reolink_host.request_vod_files.return_value = ([mock_status], [mock_vod_file])

    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}/{browse_day_0_id}")

    browse_files_id = f"FILES|{entry_id}|{TEST_CHANNEL}|{TEST_STREAM}"
    browse_file_id = f"FILE|{entry_id}|{TEST_CHANNEL}|{TEST_STREAM}|{TEST_FILE_NAME}|{TEST_START}|{TEST_END}"
    assert browse.domain == DOMAIN
    assert (
        browse.title
        == f"{TEST_CAM_NAME} lens 0 High res. {TEST_YEAR}/{TEST_MONTH}/{TEST_DAY}"
    )
    assert browse.identifier == browse_files_id
    assert browse.children[0].identifier == browse_file_id
    reolink_host.request_vod_files.assert_called_with(
        int(TEST_CHANNEL),
        TEST_START_TIME,
        TEST_END_TIME,
        stream=TEST_STREAM,
        split_time=VOD_SPLIT_TIME,
        trigger=None,
    )

    reolink_host.model = TEST_HOST_MODEL

    # browse event trigger person on a NVR
    reolink_host.is_nvr = True
    browse_event_person_id = f"EVE|{entry_id}|{TEST_CHANNEL}|{TEST_STREAM}|{TEST_YEAR}|{TEST_MONTH}|{TEST_DAY}|{VOD_trigger.PERSON.name}"

    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}/{browse_day_0_id}")
    assert browse.children[0].identifier == browse_event_person_id

    browse = await async_browse_media(
        hass, f"{URI_SCHEME}{DOMAIN}/{browse_event_person_id}"
    )

    assert browse.domain == DOMAIN
    assert (
        browse.title
        == f"{TEST_CAM_NAME} High res. {TEST_YEAR}/{TEST_MONTH}/{TEST_DAY} Person"
    )
    assert browse.identifier == browse_files_id
    assert browse.children[0].identifier == browse_file_id
    reolink_host.request_vod_files.assert_called_with(
        int(TEST_CHANNEL),
        TEST_START_TIME,
        TEST_END_TIME,
        stream=TEST_STREAM,
        split_time=VOD_SPLIT_TIME,
        trigger=VOD_trigger.PERSON,
    )