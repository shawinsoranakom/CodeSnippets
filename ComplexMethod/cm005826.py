async def test_read_flows_components_only_paginated(client: AsyncClient, logged_in_headers):
    number_of_flows = 10
    flows = [
        FlowCreate(name=f"Flow {i}", description="description", data={}, is_component=True)
        for i in range(number_of_flows)
    ]

    for flow in flows:
        response = await client.post("api/v1/flows/", json=flow.model_dump(), headers=logged_in_headers)
        assert response.status_code == 201

    response = await client.get(
        "api/v1/flows/", headers=logged_in_headers, params={"components_only": True, "get_all": False}
    )

    assert response.status_code == 200
    response_json = response.json()
    assert response_json["total"] == 10
    assert response_json["pages"] == 1
    assert response_json["page"] == 1
    assert response_json["size"] == 50
    assert all(flow["is_component"] is True for flow in response_json["items"])