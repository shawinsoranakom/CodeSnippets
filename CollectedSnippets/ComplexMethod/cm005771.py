async def test_get_all(client: AsyncClient, logged_in_headers):
    """Tests the retrieval of all available components from the API.

    Sends a GET request to the `api/v1/all` endpoint and verifies that the returned component names
    correspond to files in the components directory. Also checks for the presence of specific components
    such as "ChatInput", "Prompt", and "ChatOutput" in the response.
    """
    response = await client.get("api/v1/all", headers=logged_in_headers)
    assert response.status_code == 200
    dir_reader = DirectoryReader(BASE_COMPONENTS_PATH)
    files = dir_reader.get_files()
    # json_response is a dict of dicts
    all_names = [component_name for _, components in response.json().items() for component_name in components]
    json_response = response.json()
    # We need to test the custom nodes
    assert len(all_names) <= len(
        files
    )  # Less or equal because we might have some files that don't have the dependencies installed
    assert "ChatInput" in json_response["input_output"]
    assert "Prompt Template" in json_response["models_and_agents"]
    assert "ChatOutput" in json_response["input_output"]