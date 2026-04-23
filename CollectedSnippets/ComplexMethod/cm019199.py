async def test_browsing_h265_encoding(
    hass: HomeAssistant,
    reolink_host: MagicMock,
    config_entry: MockConfigEntry,
) -> None:
    """Test browsing a Reolink camera with h265 stream encoding."""
    entry_id = config_entry.entry_id
    reolink_host.is_nvr = True

    with patch("homeassistant.components.reolink.PLATFORMS", [Platform.CAMERA]):
        assert await hass.config_entries.async_setup(entry_id) is True
    await hass.async_block_till_done()

    browse_root_id = f"CAM|{entry_id}|{TEST_CHANNEL}"

    mock_status = MagicMock()
    mock_status.year = TEST_YEAR
    mock_status.month = TEST_MONTH
    mock_status.days = (TEST_DAY, TEST_DAY2)
    reolink_host.request_vod_files.return_value = ([mock_status], [])
    reolink_host.time.return_value = None
    reolink_host.get_encoding.return_value = "h265"
    reolink_host.supported.return_value = False

    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}/{browse_root_id}")

    browse_resolution_id = f"RESs|{entry_id}|{TEST_CHANNEL}"
    browse_res_sub_id = f"RES|{entry_id}|{TEST_CHANNEL}|sub"
    browse_res_main_id = f"RES|{entry_id}|{TEST_CHANNEL}|main"

    assert browse.domain == DOMAIN
    assert browse.title == f"{TEST_CAM_NAME}"
    assert browse.identifier == browse_resolution_id
    assert browse.children[0].identifier == browse_res_sub_id
    assert browse.children[1].identifier == browse_res_main_id

    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}/{browse_res_sub_id}")

    browse_days_id = f"DAYS|{entry_id}|{TEST_CHANNEL}|sub"
    browse_day_0_id = (
        f"DAY|{entry_id}|{TEST_CHANNEL}|sub|{TEST_YEAR}|{TEST_MONTH}|{TEST_DAY}"
    )
    browse_day_1_id = (
        f"DAY|{entry_id}|{TEST_CHANNEL}|sub|{TEST_YEAR}|{TEST_MONTH}|{TEST_DAY2}"
    )
    assert browse.domain == DOMAIN
    assert browse.title == f"{TEST_CAM_NAME} Low res."
    assert browse.identifier == browse_days_id
    assert browse.children[0].identifier == browse_day_0_id
    assert browse.children[1].identifier == browse_day_1_id