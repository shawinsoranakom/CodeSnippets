async def test_delete_folder_with_flows_with_transaction_and_build(client: AsyncClient, logged_in_headers):
    # Create a new project
    folder_name = f"Test Project {uuid4()}"
    project = FolderCreate(name=folder_name, description="Test project description", components_list=[], flows_list=[])

    response = await client.post("api/v1/projects/", json=project.model_dump(), headers=logged_in_headers)
    assert response.status_code == 201, f"Expected status code 201, but got {response.status_code}"

    created_folder = response.json()
    folder_id = created_folder["id"]

    # Create ten flows
    number_of_flows = 10
    flows = [FlowCreate(name=f"Flow {i}", description="description", data={}) for i in range(number_of_flows)]
    flow_ids = []
    for flow in flows:
        flow.folder_id = folder_id
        response = await client.post("api/v1/flows/", json=flow.model_dump(), headers=logged_in_headers)
        assert response.status_code == 201
        flow_ids.append(response.json()["id"])

    class VertexTuple(NamedTuple):
        id: str
        params: dict

    # Create a transaction for each flow
    for flow_id in flow_ids:
        await log_transaction(
            str(flow_id),
            source=VertexTuple(id="vid", params={}),
            target=VertexTuple(id="tid", params={}),
            status="success",
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

    response = await client.request("DELETE", f"api/v1/projects/{folder_id}", headers=logged_in_headers)
    assert response.status_code == 204

    for flow_id in flow_ids:
        response = await client.request(
            "GET", "api/v1/monitor/transactions", params={"flow_id": flow_id}, headers=logged_in_headers
        )
        assert response.status_code == 200, response.json()
        json_response = response.json()
        assert json_response["items"] == []

    for flow_id in flow_ids:
        response = await client.request(
            "GET", "api/v1/monitor/builds", params={"flow_id": flow_id}, headers=logged_in_headers
        )
        assert response.status_code == 200
        assert response.json() == {"vertex_builds": {}}