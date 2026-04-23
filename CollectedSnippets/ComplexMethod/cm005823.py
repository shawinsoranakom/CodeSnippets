async def test_read_flows_pagination_with_flows(client: AsyncClient, logged_in_headers):
    number_of_flows = 30
    flows = [FlowCreate(name=f"Flow {i}", description="description", data={}) for i in range(number_of_flows)]
    flow_ids = []
    for flow in flows:
        response = await client.post("api/v1/flows/", json=flow.model_dump(), headers=logged_in_headers)
        assert response.status_code == 201
        flow_ids.append(response.json()["id"])

    response = await client.get(
        "api/v1/flows/", headers=logged_in_headers, params={"page": 3, "size": 10, "get_all": False}
    )
    assert response.status_code == 200
    assert response.json()["page"] == 3
    assert response.json()["size"] == 10
    assert response.json()["pages"] == 3
    assert response.json()["total"] == number_of_flows
    assert len(response.json()["items"]) == 10

    response = await client.get(
        "api/v1/flows/", headers=logged_in_headers, params={"page": 4, "size": 10, "get_all": False}
    )
    assert response.status_code == 200
    assert response.json()["page"] == 4
    assert response.json()["size"] == 10
    assert response.json()["pages"] == 3
    assert response.json()["total"] == number_of_flows
    assert len(response.json()["items"]) == 0