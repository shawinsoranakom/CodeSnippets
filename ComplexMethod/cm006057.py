async def test_duplicate_flow_name_gaps_in_numbering(client: AsyncClient, logged_in_headers):
    """Test that gaps in numbering are handled correctly (uses max + 1)."""
    base_flow = {
        "name": "Gapped Flow",
        "description": "Test flow description",
        "data": {},
        "is_component": False,
    }

    # Create original flow
    response1 = await client.post("api/v1/flows/", json=base_flow, headers=logged_in_headers)
    assert response1.status_code == status.HTTP_201_CREATED
    assert response1.json()["name"] == "Gapped Flow"

    # Create numbered flows with gaps
    numbered_flows = [
        "Gapped Flow (1)",
        "Gapped Flow (5)",  # Gap: 2, 3, 4 missing
        "Gapped Flow (7)",  # Gap: 6 missing
    ]

    for flow_name in numbered_flows:
        numbered_flow = base_flow.copy()
        numbered_flow["name"] = flow_name
        response = await client.post("api/v1/flows/", json=numbered_flow, headers=logged_in_headers)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["name"] == flow_name

    # Create another duplicate - should use max(1,5,7) + 1 = 8
    response_final = await client.post("api/v1/flows/", json=base_flow, headers=logged_in_headers)
    assert response_final.status_code == status.HTTP_201_CREATED
    assert response_final.json()["name"] == "Gapped Flow (8)"