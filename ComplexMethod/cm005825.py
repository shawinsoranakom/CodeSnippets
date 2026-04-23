async def test_read_flows_no_pagination_params(client: AsyncClient, logged_in_headers):
    number_of_flows = 30
    flows = [FlowCreate(name=f"Flow {i}", description="description", data={}) for i in range(number_of_flows)]
    for flow in flows:
        response = await client.post("api/v1/flows/", json=flow.model_dump(), headers=logged_in_headers)
        assert response.status_code == 201

    response = await client.get("api/v1/flows/", headers=logged_in_headers, params={"get_all": False})
    assert response.status_code == 200
    # Assert default pagination values, adjust these according to your API's default behavior
    assert response.json()["page"] == 1
    assert response.json()["size"] == 50
    assert response.json()["pages"] == 1
    assert response.json()["total"] == number_of_flows
    assert len(response.json()["items"]) == number_of_flows