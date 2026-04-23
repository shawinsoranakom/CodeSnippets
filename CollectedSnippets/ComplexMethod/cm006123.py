async def test_download_file_starter_project(client: AsyncClient, logged_in_headers, active_user, json_flow):
    """Test downloading a project with multiple flows.

    This test specifically validates:
    1. The download endpoint returns a valid ZIP file with multiple flows
    2. The remove_api_keys function handles flows with various template structures,
       including components that don't have 'name' keys in their template values
       (e.g., Note components with only backgroundColor)
    3. API keys are removed from downloaded flows
    4. Non-sensitive data is preserved in the download
    """
    # Create a project for the user (since download_file requires user ownership)
    project_payload = {
        "name": STARTER_FOLDER_NAME,
        "description": "Starter projects to help you get started in Langflow.",
        "flows_list": [],
        "components_list": [],
    }
    create_response = await client.post("api/v1/projects/", json=project_payload, headers=logged_in_headers)
    assert create_response.status_code == status.HTTP_201_CREATED
    starter_project = create_response.json()
    starter_project_id = starter_project["id"]

    # Create multiple flows in the project
    flow_data = json.loads(json_flow)

    # Create a flow with a Note component to test the bug fix
    # Note components have template values without 'name' keys
    flow_with_note = {
        "nodes": [
            {
                "id": "note-1",
                "type": "genericNode",
                "data": {
                    "node": {
                        "template": {
                            "backgroundColor": {"value": "#ffffff"},  # No 'name' key
                            "text": {"value": "Test note"},  # No 'name' key
                        }
                    }
                },
            },
            # Add a node with API keys to test removal
            {
                "id": "api-node-1",
                "type": "genericNode",
                "data": {
                    "node": {
                        "template": {
                            "api_key": {
                                "name": "api_key",
                                "value": "secret-key-123",
                                "password": True,
                            },
                            "regular_field": {"name": "regular_field", "value": "keep-this"},
                        }
                    }
                },
            },
        ],
        "edges": [],
    }

    flows_created = []
    async with session_scope() as session:
        # Create 3 flows: 2 from basic example + 1 with Note component
        for i in range(2):
            flow_create = FlowCreate(
                name=f"Starter Flow {i + 1}",
                description=f"Test starter flow {i + 1}",
                data=flow_data.get("data", {}),
                folder_id=starter_project_id,
                user_id=active_user.id,
            )
            flow = Flow.model_validate(flow_create.model_dump(exclude={"id"}))
            session.add(flow)
            flows_created.append(flow)

        # Add flow with Note component
        flow_create_note = FlowCreate(
            name="Flow with Note",
            description="Flow with Note component and API keys",
            data=flow_with_note,
            folder_id=starter_project_id,
            user_id=active_user.id,
        )
        flow_note = Flow.model_validate(flow_create_note.model_dump(exclude={"id"}))
        session.add(flow_note)
        flows_created.append(flow_note)

        await session.flush()
        # Refresh to get IDs
        for flow in flows_created:
            await session.refresh(flow)
        await session.commit()

    # Download the starter project
    response = await client.get(
        f"api/v1/projects/download/{starter_project_id}",
        headers=logged_in_headers,
    )

    # Verify response
    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.headers["Content-Type"] == "application/x-zip-compressed"
    assert "attachment" in response.headers["Content-Disposition"]
    assert "filename" in response.headers["Content-Disposition"]
    # The filename is URL-encoded in the header, so check for the project name
    content_disposition = response.headers["Content-Disposition"]
    assert (
        STARTER_FOLDER_NAME.replace(" ", "%20") in content_disposition
        or STARTER_FOLDER_NAME.replace(" ", "_") in content_disposition
    )

    # Verify zip file contents
    zip_content = response.content
    with zipfile.ZipFile(io.BytesIO(zip_content), "r") as zip_file:
        file_names = zip_file.namelist()
        # Should have 3 flow files
        assert len(file_names) == 3, f"Expected 3 files in zip, got {len(file_names)}: {file_names}"

        # Verify each basic flow file exists and contains valid JSON
        for i in range(2):
            expected_filename = f"Starter Flow {i + 1}.json"
            assert expected_filename in file_names, f"Expected {expected_filename} in zip file"

            # Read and verify flow content
            flow_content = zip_file.read(expected_filename)
            flow_json = json.loads(flow_content)
            assert flow_json["name"] == f"Starter Flow {i + 1}"
            assert flow_json["description"] == f"Test starter flow {i + 1}"

        # Verify the flow with Note component
        note_flow_filename = "Flow with Note.json"
        assert note_flow_filename in file_names, f"Expected {note_flow_filename} in zip file"

        # Read and verify the Note flow - this tests the bug fix
        note_flow_content = zip_file.read(note_flow_filename)
        note_flow_json = json.loads(note_flow_content)
        assert note_flow_json["name"] == "Flow with Note"
        assert note_flow_json["description"] == "Flow with Note component and API keys"

        # Verify the flow has the expected structure
        assert "data" in note_flow_json
        assert "nodes" in note_flow_json["data"]
        assert len(note_flow_json["data"]["nodes"]) == 2
        # Find the API node and verify API key was removed
        api_node = None
        note_node = None
        for node in note_flow_json["data"]["nodes"]:
            if node["id"] == "api-node-1":
                api_node = node
            elif node["id"] == "note-1":
                note_node = node

        # Verify Note node exists and didn't cause errors (the bug fix)
        assert note_node is not None, "Note node should exist in downloaded flow"
        note_template = note_node["data"]["node"]["template"]
        assert "backgroundColor" in note_template, "Note backgroundColor should be preserved"
        assert "text" in note_template, "Note text should be preserved"

        # Verify API key was removed but regular field was kept
        assert api_node is not None, "API node should exist in downloaded flow"
        api_template = api_node["data"]["node"]["template"]
        assert "api_key" in api_template, "API key field should exist"
        assert api_template["api_key"]["value"] is None, "API key value should be removed/null"
        assert "regular_field" in api_template, "Regular field should be preserved"
        assert api_template["regular_field"]["value"] == "keep-this", "Regular field value should be kept"

    # Clean up: delete the project (which will cascade delete flows)
    delete_response = await client.delete(f"api/v1/projects/{starter_project_id}", headers=logged_in_headers)
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT