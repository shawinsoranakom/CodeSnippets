async def test_sync_flows_from_fs(client: AsyncClient, logged_in_headers):
    # Use a relative path which will be placed in the user's flows directory
    # The path validation requires paths to be within the user's flows directory for security
    flow_filename = f"{uuid.uuid4()}.json"
    try:
        basic_case = {
            "name": "string",
            "description": "string",
            "data": {},
            "locked": False,
            "fs_path": flow_filename,
        }
        response = await client.post("api/v1/flows/", json=basic_case, headers=logged_in_headers)
        assert response.status_code == 201, f"Failed to create flow: {response.text}"
        created_flow = response.json()
        flow_id = created_flow["id"]
        user_id = created_flow["user_id"]

        # Construct the full path where the file was saved
        # The API saves relative paths to: storage_service.data_dir / "flows" / user_id / filename
        from langflow.services.deps import get_storage_service

        storage_service = get_storage_service()
        flow_file = storage_service.data_dir / "flows" / str(user_id) / flow_filename

        # Read the file created by the API
        content = await flow_file.read_text(encoding="utf-8")
        fs_flow = Flow.model_validate_json(content)
        fs_flow.name = "new name"
        fs_flow.description = "new description"
        fs_flow.data = {"nodes": {}, "edges": {}}
        fs_flow.locked = True

        await flow_file.write_text(fs_flow.model_dump_json(), encoding="utf-8")

        result = {}
        for i in range(10):
            response = await client.get(f"api/v1/flows/{flow_id}", headers=logged_in_headers)
            result = response.json()
            if result["name"] == "new name":
                break
            assert i != 9, "flow name should have been updated"
            await asyncio.sleep(0.1)

        assert result["description"] == "new description"
        assert result["data"] == {"nodes": {}, "edges": {}}
        assert result["locked"] is True
    finally:
        if "flow_file" in locals():
            await flow_file.unlink(missing_ok=True)