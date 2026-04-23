async def test_delete_flows_with_transaction_and_build(client: AsyncClient, logged_in_headers):
    # Create ten flows
    number_of_flows = 10
    flows = [FlowCreate(name=f"Flow {i}", description="description", data={}) for i in range(number_of_flows)]
    flow_ids = []
    for flow in flows:
        response = await client.post("api/v1/flows/", json=flow.model_dump(), headers=logged_in_headers)
        assert response.status_code == 201
        flow_ids.append(response.json()["id"])

    class VertexTuple(NamedTuple):
        id: str

    # Create a transaction for each flow
    for flow_id in flow_ids:
        await log_transaction(
            str(flow_id), source=VertexTuple(id="vid"), target=VertexTuple(id="tid"), status="success"
        )

    # Create a build for each flow
    for flow_id in flow_ids:
        build = {
            "valid": True,
            "params": {},
            "data": ResultDataResponse(),
            "artifacts": {},
            "vertex_id": "vid",
            "flow_id": flow_id,
        }
        await log_vertex_build(
            flow_id=build["flow_id"],
            vertex_id=build["vertex_id"],
            valid=build["valid"],
            params=build["params"],
            data=build["data"],
            artifacts=build.get("artifacts"),
        )

    response = await client.request("DELETE", "api/v1/flows/", headers=logged_in_headers, json=flow_ids)
    assert response.status_code == 200, response.content
    assert response.json().get("deleted") == number_of_flows

    for flow_id in flow_ids:
        response = await client.request(
            "GET", "api/v1/monitor/transactions", params={"flow_id": flow_id}, headers=logged_in_headers
        )
        assert response.status_code == 200
        json_response = response.json()
        assert json_response["items"] == []

    for flow_id in flow_ids:
        response = await client.request(
            "GET", "api/v1/monitor/builds", params={"flow_id": flow_id}, headers=logged_in_headers
        )
        assert response.status_code == 200
        assert response.json() == {"vertex_builds": {}}