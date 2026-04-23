async def test_notify_file(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_is_allowed_path: MagicMock,
    timestamp: bool,
    domain: str,
    service: str,
    params: dict[str, str],
) -> None:
    """Test the notify file output."""
    filename = "mock_file"
    full_filename = os.path.join(hass.config.path(), filename)

    message = params["message"]

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"name": "test", "platform": "notify", "file_path": full_filename},
        options={"timestamp": timestamp},
        version=2,
        title=f"test [{filename}]",
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)

    freezer.move_to(dt_util.utcnow())

    m_open = mock_open()
    with (
        patch("homeassistant.components.file.notify.open", m_open, create=True),
        patch("homeassistant.components.file.notify.os.stat") as mock_st,
    ):
        mock_st.return_value.st_size = 0
        title = (
            f"{ATTR_TITLE_DEFAULT} notifications "
            f"(Log started: {dt_util.utcnow().isoformat()})\n{'-' * 80}\n"
        )

        await hass.services.async_call(domain, service, params, blocking=True)

        assert m_open.call_count == 1
        assert m_open.call_args == call(full_filename, "a", encoding="utf8")

        assert m_open.return_value.write.call_count == 2
        if not timestamp:
            assert m_open.return_value.write.call_args_list == [
                call(title),
                call(f"{message}\n"),
            ]
        else:
            assert m_open.return_value.write.call_args_list == [
                call(title),
                call(f"{dt_util.utcnow().isoformat()} {message}\n"),
            ]