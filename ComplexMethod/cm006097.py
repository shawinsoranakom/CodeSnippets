async def test_flow_created_is_retrievable_in_folder(client: AsyncClient, logged_in_headers):
    """Test that a created flow can be retrieved by listing flows in its folder.

    This verifies the flow is not orphaned and appears in the UI.
    """
    # Configure client to follow redirects
    client.follow_redirects = True

    # Create a flow
    flow_data = {
        "name": "Retrievable Flow",
        "data": {},
    }
    create_response = await client.post("api/v1/flows/", json=flow_data, headers=logged_in_headers)
    assert create_response.status_code == status.HTTP_201_CREATED
    flow_id = create_response.json()["id"]
    folder_id = create_response.json()["folder_id"]

    # List flows in the folder
    response = await client.get(f"api/v1/folders/{folder_id}", headers=logged_in_headers)
    assert response.status_code == status.HTTP_200_OK

    # Check if the flow is in the folder's flows list
    result = response.json()
    # Handle different response structures
    if "flows" in result:
        flows = result["flows"]
    elif "folder" in result and "flows" in result["folder"]:
        flows = result["folder"]["flows"]
    else:
        # Response might be paginated or have different structure
        flows = result.get("flows", [])

    # Get flow IDs from the response
    flow_ids_in_folder = [f["id"] if isinstance(f, dict) else str(f) for f in flows]

    # The created flow should be in the folder's flow list
    assert flow_id in flow_ids_in_folder, f"Flow {flow_id} should be retrievable in folder {folder_id}"