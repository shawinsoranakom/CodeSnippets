async def test_read_flows_custom_page_size(client: AsyncClient, logged_in_headers):
    number_of_flows = 30
    flows = [FlowCreate(name=f"Flow {i}", description="description", data={}) for i in range(number_of_flows)]
    for flow in flows:
        response = await client.post("api/v1/flows/", json=flow.model_dump(), headers=logged_in_headers)
        assert response.status_code == 201

    response = await client.get(
        "api/v1/flows/", headers=logged_in_headers, params={"page": 1, "size": 15, "get_all": False}
    )
    assert response.status_code == 200
    assert response.json()["page"] == 1
    assert response.json()["size"] == 15
    assert response.json()["pages"] == 2
    assert response.json()["total"] == number_of_flows
    assert len(response.json()["items"]) == 15