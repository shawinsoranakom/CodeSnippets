async def test_download_single_flow_returns_normalized_json(client: AsyncClient, logged_in_headers):
    """Downloading a single flow returns normalized JSON rather than a ZIP archive."""
    code_value = "print('hello')\nprint('world')"
    flow_payload = FlowCreate(
        name=str(uuid4()),
        description="single flow export",
        data={
            "nodes": [
                {
                    "id": "node-1",
                    "data": {
                        "node": {
                            "template": {
                                "code": {"type": "code", "value": code_value},
                                "api_key": {"name": "api_key", "password": True, "value": "super-secret"},
                            }
                        }
                    },
                }
            ],
            "edges": [],
        },
    )

    create_response = await client.post("api/v1/flows/", json=flow_payload.model_dump(), headers=logged_in_headers)
    assert create_response.status_code == 201
    flow_id = create_response.json()["id"]

    download_response = await client.post(
        "api/v1/flows/download/",
        data=json.dumps([flow_id]),
        headers={**logged_in_headers, "Content-Type": "application/json"},
    )
    assert download_response.status_code == 200
    assert download_response.headers["Content-Type"].startswith("application/json")

    downloaded = download_response.json()
    assert downloaded["name"] == flow_payload.name
    assert "updated_at" not in downloaded
    assert "user_id" not in downloaded
    assert "folder_id" not in downloaded
    assert "access_type" not in downloaded
    assert downloaded["data"]["nodes"][0]["data"]["node"]["template"]["code"]["value"] == [
        "print('hello')",
        "print('world')",
    ]
    assert downloaded["data"]["nodes"][0]["data"]["node"]["template"]["api_key"]["value"] is None