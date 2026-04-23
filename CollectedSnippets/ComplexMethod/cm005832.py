async def test_upload_file(client: AsyncClient, json_flow: str, logged_in_headers):
    flow = orjson.loads(json_flow)
    data = flow["data"]
    # Create test data
    flow_unique_name = str(uuid4())
    flow_2_unique_name = str(uuid4())
    flow_list = FlowListCreate(
        flows=[
            FlowCreate(name=flow_unique_name, description="description", data=data),
            FlowCreate(name=flow_2_unique_name, description="description", data=data),
        ]
    )
    file_contents = orjson_dumps(flow_list.dict())
    response = await client.post(
        "api/v1/flows/upload/",
        files={"file": ("examples.json", file_contents, "application/json")},
        headers=logged_in_headers,
    )
    # Check response status code
    assert response.status_code == 201
    # Check response data
    response_data = response.json()
    assert len(response_data) == 2
    assert flow_unique_name in response_data[0]["name"]
    assert response_data[0]["description"] == "description"
    assert response_data[0]["data"] == data
    assert response_data[1]["name"] == flow_2_unique_name
    assert response_data[1]["description"] == "description"
    assert response_data[1]["data"] == data