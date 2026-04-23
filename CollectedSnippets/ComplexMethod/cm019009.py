async def test_deprecated_voice(
    hass: HomeAssistant,
    issue_registry: ir.IssueRegistry,
    cloud: MagicMock,
    hass_client: ClientSessionGenerator,
    data: dict[str, Any],
    expected_url_suffix: str,
) -> None:
    """Test we create an issue when a deprecated voice is used for text-to-speech."""
    language = "zh-CN"
    deprecated_voice = "XiaoxuanNeural"
    replacement_voice = "XiaozhenNeural"
    mock_process_tts = AsyncMock(
        return_value=b"",
    )
    cloud.voice.process_tts = mock_process_tts
    mock_process_tts_stream = _make_stream_mock("There is someone at the door.")
    cloud.voice.process_tts_stream = mock_process_tts_stream

    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {}})
    await hass.async_block_till_done()
    await cloud.login("test-user", "test-pass")
    client = await hass_client()

    # Test with non deprecated voice.
    with patch(
        "homeassistant.components.tts.secrets.token_urlsafe", return_value="test_token"
    ):
        url = "/api/tts_get_url"
        data |= {
            "message": "There is someone at the door.",
            "language": language,
            "options": {"voice": replacement_voice},
        }

        req = await client.post(url, json=data)
        assert req.status == HTTPStatus.OK
        response = await req.json()

        assert response == {
            "url": ("http://example.local:8123/api/tts_proxy/test_token.mp3"),
            "path": ("/api/tts_proxy/test_token.mp3"),
        }
        await hass.async_block_till_done()

        # Force streaming
        await client.get(response["path"])

    if data.get("engine_id", "").startswith("tts."):
        # Streaming
        assert mock_process_tts_stream.call_count == 1
        assert mock_process_tts_stream.call_args is not None
        assert mock_process_tts_stream.call_args.kwargs["language"] == language
        assert mock_process_tts_stream.call_args.kwargs["gender"] is None
        assert mock_process_tts_stream.call_args.kwargs["voice"] == replacement_voice
    else:
        # Non-streaming
        assert mock_process_tts.call_count == 1
        assert mock_process_tts.call_args is not None
        assert (
            mock_process_tts.call_args.kwargs["text"] == "There is someone at the door."
        )
        assert mock_process_tts.call_args.kwargs["language"] == language
        assert mock_process_tts.call_args.kwargs["gender"] is None
        assert mock_process_tts.call_args.kwargs["voice"] == replacement_voice
        assert mock_process_tts.call_args.kwargs["output"] == "mp3"

    issue = issue_registry.async_get_issue(
        "cloud", f"deprecated_voice_{replacement_voice}"
    )
    assert issue is None
    mock_process_tts.reset_mock()
    mock_process_tts_stream.reset_mock()

    # Test with deprecated voice.
    data["options"] = {"voice": deprecated_voice}

    with patch(
        "homeassistant.components.tts.secrets.token_urlsafe", return_value="test_token"
    ):
        req = await client.post(url, json=data)
        assert req.status == HTTPStatus.OK
        response = await req.json()

        assert response == {
            "url": ("http://example.local:8123/api/tts_proxy/test_token.mp3"),
            "path": ("/api/tts_proxy/test_token.mp3"),
        }
        await hass.async_block_till_done()

        # Force streaming
        await client.get(response["path"])

    issue_id = f"deprecated_voice_{deprecated_voice}"

    if data.get("engine_id", "").startswith("tts."):
        # Streaming
        assert mock_process_tts_stream.call_count == 1
        assert mock_process_tts_stream.call_args is not None
        assert mock_process_tts_stream.call_args.kwargs["language"] == language
        assert mock_process_tts_stream.call_args.kwargs["gender"] is None
        assert mock_process_tts_stream.call_args.kwargs["voice"] == replacement_voice
    else:
        # Non-streaming
        assert mock_process_tts.call_count == 1
        assert mock_process_tts.call_args is not None
        assert (
            mock_process_tts.call_args.kwargs["text"] == "There is someone at the door."
        )
        assert mock_process_tts.call_args.kwargs["language"] == language
        assert mock_process_tts.call_args.kwargs["gender"] is None
        assert mock_process_tts.call_args.kwargs["voice"] == replacement_voice
        assert mock_process_tts.call_args.kwargs["output"] == "mp3"

    issue = issue_registry.async_get_issue("cloud", issue_id)
    assert issue is not None
    assert issue.breaks_in_ha_version == "2024.8.0"
    assert issue.is_fixable is True
    assert issue.is_persistent is True
    assert issue.severity == ir.IssueSeverity.WARNING
    assert issue.translation_key == "deprecated_voice"
    assert issue.translation_placeholders == {
        "deprecated_voice": deprecated_voice,
        "replacement_voice": replacement_voice,
    }

    resp = await client.post(
        "/api/repairs/issues/fix",
        json={"handler": DOMAIN, "issue_id": issue.issue_id},
    )

    assert resp.status == HTTPStatus.OK
    data = await resp.json()

    flow_id = data["flow_id"]
    assert data == {
        "type": "form",
        "flow_id": flow_id,
        "handler": DOMAIN,
        "step_id": "confirm",
        "data_schema": [],
        "errors": None,
        "description_placeholders": {
            "deprecated_voice": "XiaoxuanNeural",
            "replacement_voice": "XiaozhenNeural",
        },
        "last_step": None,
        "preview": None,
    }

    resp = await client.post(f"/api/repairs/issues/fix/{flow_id}")

    assert resp.status == HTTPStatus.OK
    data = await resp.json()

    flow_id = data["flow_id"]
    assert data == {
        "type": "create_entry",
        "flow_id": flow_id,
        "handler": DOMAIN,
        "description": None,
        "description_placeholders": None,
    }

    assert not issue_registry.async_get_issue(DOMAIN, issue_id)