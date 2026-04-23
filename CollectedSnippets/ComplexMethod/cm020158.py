async def test_agent_upload(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    hass_ws_client: WebSocketGenerator,
    supervisor_client: AsyncMock,
) -> None:
    """Test agent upload backup."""
    client = await hass_client()
    ws_client = await hass_ws_client(hass)
    # First call: reader_writer gets backup details after receiving the file.
    # Second call: agent's async_get_backup check raises not found so the
    # agent proceeds with the upload instead of skipping it.
    supervisor_client.backups.backup_info.side_effect = [
        TEST_BACKUP_DETAILS,
        SupervisorNotFoundError(),
    ]

    upload_call_bytes: list[bytearray] = []

    async def mock_upload(
        stream: AsyncIterator[bytes], *args: Any, **kwargs: Any
    ) -> str:
        """Mock upload that consumes the wrapped stream."""
        received = bytearray()
        async for chunk in stream:
            received.extend(chunk)
        upload_call_bytes.append(received)
        return TEST_BACKUP_DETAILS.slug

    supervisor_client.backups.upload_backup.side_effect = mock_upload
    supervisor_client.backups.download_backup.return_value.__aiter__.return_value = (
        iter((b"backup data",))
    )

    await ws_client.send_json_auto_id({"type": "backup/subscribe_events"})
    response = await ws_client.receive_json()
    assert response["event"] == {"manager_state": "idle"}
    response = await ws_client.receive_json()
    assert response["success"] is True

    supervisor_client.backups.reload.assert_not_called()
    resp = await client.post(
        "/api/backup/upload?agent_id=hassio.local",
        data={"file": StringIO("test")},
    )
    await hass.async_block_till_done()

    assert resp.status == 201
    # First upload call: reader_writer receives the raw upload stream.
    assert upload_call_bytes[0] == b"test"
    # Second upload call: agent uploads via stream_with_progress wrapper.
    assert upload_call_bytes[1] == b"backup data"
    supervisor_client.backups.reload.assert_not_called()
    supervisor_client.backups.download_backup.assert_called_once()
    supervisor_client.backups.remove_backup.assert_not_called()

    # Verify upload progress events were emitted
    upload_progress_events: list[dict[str, Any]] = []
    while True:
        response = await ws_client.receive_json()
        event = response.get("event")
        if event is None:
            continue
        if "uploaded_bytes" in event and event.get("agent_id") == "hassio.local":
            upload_progress_events.append(event)
        if event == {"manager_state": "idle"}:
            break

    assert upload_progress_events
    # Verify at least one event had uploaded_bytes less than total_bytes
    assert any(
        event["uploaded_bytes"] < event["total_bytes"]
        for event in upload_progress_events
    )
    # Verify all events had uploaded_bytes less than or equal to total_bytes
    assert all(
        event["uploaded_bytes"] <= event["total_bytes"]
        for event in upload_progress_events
    )