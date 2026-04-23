async def test_services(
    hass: HomeAssistant, mock_imap_protocol: MagicMock, message_parts: dict[str, Any]
) -> None:
    """Test receiving a message successfully."""
    event_called = async_capture_events(hass, "imap_content")

    config = MOCK_CONFIG.copy()
    config_entry = MockConfigEntry(domain=DOMAIN, data=config)
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    # Make sure we have had one update (when polling)
    async_fire_time_changed(hass, utcnow() + timedelta(seconds=5))
    await hass.async_block_till_done()
    state = hass.states.get("sensor.imap_email_email_com_messages")
    # we should have received one message
    assert state is not None
    assert state.state == "1"
    assert state.attributes["state_class"] == SensorStateClass.MEASUREMENT

    # we should have received one event
    assert len(event_called) == 1
    data: dict[str, Any] = event_called[0].data
    assert data["server"] == "imap.server.com"
    assert data["username"] == "email@email.com"
    assert data["search"] == "UnSeen UnDeleted"
    assert data["folder"] == "INBOX"
    assert data["sender"] == "john.doe@example.com"
    assert data["subject"] == "Test subject"
    assert data["uid"] == "1"
    assert data["entry_id"] == config_entry.entry_id
    assert data["parts"] == message_parts

    # Test seen service
    data = {"entry": config_entry.entry_id, "uid": "1"}
    await hass.services.async_call(DOMAIN, "seen", data, blocking=True)
    mock_imap_protocol.store.assert_called_with("1", "+FLAGS (\\Seen)")
    mock_imap_protocol.store.reset_mock()

    # Test move service
    data = {
        "entry": config_entry.entry_id,
        "uid": "1",
        "seen": True,
        "target_folder": "Trash",
    }
    await hass.services.async_call(DOMAIN, "move", data, blocking=True)
    mock_imap_protocol.store.assert_has_calls(
        [call("1", "+FLAGS (\\Seen)"), call("1", "+FLAGS (\\Deleted)")]
    )
    mock_imap_protocol.copy.assert_called_with("1", "Trash")
    mock_imap_protocol.protocol.expunge.assert_called_once()
    mock_imap_protocol.store.reset_mock()
    mock_imap_protocol.copy.reset_mock()
    mock_imap_protocol.protocol.expunge.reset_mock()

    # Test delete service
    data = {"entry": config_entry.entry_id, "uid": "1"}
    await hass.services.async_call(DOMAIN, "delete", data, blocking=True)
    mock_imap_protocol.store.assert_called_with("1", "+FLAGS (\\Deleted)")
    mock_imap_protocol.protocol.expunge.assert_called_once()

    # Test fetch service with text response
    mock_imap_protocol.reset_mock()
    data = {"entry": config_entry.entry_id, "uid": "1"}
    response = await hass.services.async_call(
        DOMAIN, "fetch", data, blocking=True, return_response=True
    )
    mock_imap_protocol.fetch.assert_called_with("1", "BODY.PEEK[]")
    assert response["text"] == "*Multi* part Test body\n"
    assert response["sender"] == "john.doe@example.com"
    assert response["subject"] == "Test subject"
    assert response["uid"] == "1"
    assert response["parts"] == message_parts

    # Test fetch part service with attachment response
    mock_imap_protocol.reset_mock()
    data = {"entry": config_entry.entry_id, "uid": "1", "part": "1"}
    response = await hass.services.async_call(
        DOMAIN, "fetch_part", data, blocking=True, return_response=True
    )
    mock_imap_protocol.fetch.assert_called_with("1", "BODY.PEEK[]")
    assert response["part_data"] == "VGV4dCBhdHRhY2htZW50IGNvbnRlbnQ=\n"
    assert response["content_type"] == "text/plain"
    assert response["content_transfer_encoding"] == "base64"
    assert response["filename"] == "Text attachment content.txt"
    assert response["part"] == "1"
    assert response["uid"] == "1"
    assert b64decode(response["part_data"]) == b"Text attachment content"

    # Test fetch part service with invalid part index
    for part in ("A", "2", "0"):
        data = {"entry": config_entry.entry_id, "uid": "1", "part": part}
        with pytest.raises(ServiceValidationError) as exc:
            await hass.services.async_call(
                DOMAIN, "fetch_part", data, blocking=True, return_response=True
            )
        assert exc.value.translation_key == "invalid_part_index"

    # Test with invalid entry_id
    data = {"entry": "invalid", "uid": "1"}
    with pytest.raises(ServiceValidationError) as exc:
        await hass.services.async_call(DOMAIN, "seen", data, blocking=True)
    assert exc.value.translation_domain == DOMAIN
    assert exc.value.translation_key == "invalid_entry"

    # Test processing imap client failures
    exceptions = {
        "invalid_auth": {"exc": InvalidAuth(), "translation_placeholders": None},
        "invalid_folder": {"exc": InvalidFolder(), "translation_placeholders": None},
        "imap_server_fail": {
            "exc": AioImapException("Bla"),
            "translation_placeholders": {"error": "Bla"},
        },
    }
    for translation_key, attrs in exceptions.items():
        with patch(
            "homeassistant.components.imap.connect_to_server", side_effect=attrs["exc"]
        ):
            data = {"entry": config_entry.entry_id, "uid": "1"}
            with pytest.raises(ServiceValidationError) as exc:
                await hass.services.async_call(DOMAIN, "seen", data, blocking=True)
            assert exc.value.translation_domain == DOMAIN
            assert exc.value.translation_key == translation_key
            assert (
                exc.value.translation_placeholders == attrs["translation_placeholders"]
            )

    # Test unexpected errors with storing a flag during a service call
    service_calls_response = {
        "seen": ({"entry": config_entry.entry_id, "uid": "1"}, False),
        "move": (
            {
                "entry": config_entry.entry_id,
                "uid": "1",
                "seen": False,
                "target_folder": "Trash",
            },
            False,
        ),
        "delete": ({"entry": config_entry.entry_id, "uid": "1"}, False),
        "fetch": ({"entry": config_entry.entry_id, "uid": "1"}, True),
        "fetch_part": ({"entry": config_entry.entry_id, "uid": "1", "part": "1"}, True),
    }
    patch_error_translation_key = {
        "seen": ("store", "seen_failed"),
        "move": ("copy", "copy_failed"),
        "delete": ("store", "delete_failed"),
        "fetch": ("fetch", "fetch_failed"),
        "fetch_part": ("fetch", "fetch_failed"),
    }
    for service, (data, response) in service_calls_response.items():
        with (
            pytest.raises(ServiceValidationError) as exc,
            patch.object(
                mock_imap_protocol,
                patch_error_translation_key[service][0],
                side_effect=AioImapException("Bla"),
            ),
        ):
            await hass.services.async_call(
                DOMAIN, service, data, blocking=True, return_response=response
            )
        assert exc.value.translation_domain == DOMAIN
        assert exc.value.translation_key == "imap_server_fail"
        assert exc.value.translation_placeholders == {"error": "Bla"}
        # Test with bad responses
        with (
            pytest.raises(ServiceValidationError) as exc,
            patch.object(
                mock_imap_protocol,
                patch_error_translation_key[service][0],
                return_value=Response("BAD", [b"Bla"]),
            ),
        ):
            await hass.services.async_call(
                DOMAIN, service, data, blocking=True, return_response=response
            )
        assert exc.value.translation_domain == DOMAIN
        assert exc.value.translation_key == patch_error_translation_key[service][1]
        assert exc.value.translation_placeholders == {"error": "Bla"}