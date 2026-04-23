async def test_full_lifecycle(client: AsyncClient, logged_in_headers):
    """End-to-end: create, snapshot, edit, snapshot, activate old, verify."""
    # 1. Create flow with initial data
    flow = await _create_flow(client, logged_in_headers)
    flow_id = flow["id"]
    initial_data = flow["data"]

    # 2. Save v1 snapshot
    v1 = await _create_snapshot(client, logged_in_headers, flow_id, description="version 1")
    assert v1["version_number"] == 1

    # 3. Edit the flow
    data_v2 = {"nodes": [{"id": "n1"}, {"id": "n2"}], "edges": [{"id": "e1"}]}
    await _patch_flow_data(client, logged_in_headers, flow_id, data_v2)

    # 4. Save v2 snapshot
    v2 = await _create_snapshot(client, logged_in_headers, flow_id, description="version 2")
    assert v2["version_number"] == 2

    # 5. Edit the flow again
    data_v3 = {"nodes": [{"id": "n1"}, {"id": "n2"}, {"id": "n3"}], "edges": []}
    await _patch_flow_data(client, logged_in_headers, flow_id, data_v3)

    # 6. Activate v1 — should auto-snapshot current state, then revert to v1's data
    resp = await client.post(f"api/v1/flows/{flow_id}/versions/{v1['id']}/activate", headers=logged_in_headers)
    assert resp.status_code == status.HTTP_200_OK
    activated_flow = resp.json()
    assert activated_flow["data"] == initial_data

    # 7. Verify versions now has 3 entries: v1, v2, + auto-snapshot (v3)
    entries = await _list_versions(client, logged_in_headers, flow_id)
    assert len(entries) == 3

    # 8. The auto-snapshot should contain data_v3
    auto = next(e for e in entries if "Auto-saved" in (e["description"] or ""))
    auto_full = await client.get(f"api/v1/flows/{flow_id}/versions/{auto['id']}", headers=logged_in_headers)
    assert auto_full.json()["data"] == data_v3

    # 9. Activate v2
    resp2 = await client.post(f"api/v1/flows/{flow_id}/versions/{v2['id']}/activate", headers=logged_in_headers)
    assert resp2.status_code == status.HTTP_200_OK
    assert resp2.json()["data"] == data_v2