async def test_list_versions_pagination(client: AsyncClient, logged_in_headers):
    flow = await _create_flow(client, logged_in_headers)

    # Create 5 snapshots
    for i in range(5):
        await _create_snapshot(client, logged_in_headers, flow["id"], description=f"snap-{i}")

    # Fetch with limit=2
    resp = await client.get(
        f"api/v1/flows/{flow['id']}/versions/",
        params={"limit": 2, "offset": 0},
        headers=logged_in_headers,
    )
    assert resp.status_code == status.HTTP_200_OK
    page1 = resp.json()["entries"]
    assert len(page1) == 2
    assert page1[0]["version_number"] == 5  # newest first
    assert page1[1]["version_number"] == 4

    # Second page
    resp = await client.get(
        f"api/v1/flows/{flow['id']}/versions/",
        params={"limit": 2, "offset": 2},
        headers=logged_in_headers,
    )
    page2 = resp.json()["entries"]
    assert len(page2) == 2
    assert page2[0]["version_number"] == 3