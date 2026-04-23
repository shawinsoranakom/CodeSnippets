async def test_pruning_deletes_oldest_by_data_content(client: AsyncClient, logged_in_headers, monkeypatch):
    """Verify that pruned entries are truly the oldest by checking surviving data content."""
    from langflow.services.deps import get_settings_service

    settings = get_settings_service().settings
    monkeypatch.setattr(settings, "max_flow_version_entries_per_flow", 2)

    flow = await _create_flow(client, logged_in_headers)
    flow_id = flow["id"]

    # Create 3 snapshots, each with distinct flow data so we can verify which survived.
    for i in range(3):
        data = {"nodes": [{"id": f"node-from-snap-{i}"}], "edges": []}
        await _patch_flow_data(client, logged_in_headers, flow_id, data)
        await _create_snapshot(client, logged_in_headers, flow_id, description=f"snap-{i}")

    # Only the 2 newest should survive (snap-1 and snap-2); snap-0 should be pruned.
    entries = await _list_versions(client, logged_in_headers, flow_id)
    assert len(entries) == 2
    assert entries[0]["description"] == "snap-2"
    assert entries[1]["description"] == "snap-1"

    # Fetch full data for each survivor and confirm it matches the expected snapshot data.
    for entry, expected_idx in zip(entries, [2, 1], strict=False):
        resp = await client.get(
            f"api/v1/flows/{flow_id}/versions/{entry['id']}",
            headers=logged_in_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["nodes"][0]["id"] == f"node-from-snap-{expected_idx}"