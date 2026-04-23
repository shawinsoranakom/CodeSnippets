async def test_list_profile_pictures_empty_response_format(empty_config_dir, files_client):  # noqa: ARG001
    """Test that the list response format is correct even with fallback.

    The response should always have the correct format: {"files": [...]}
    """
    response = await files_client.get("api/v1/files/profile_pictures/list")
    assert response.status_code == 200

    data = response.json()

    # Verify response structure
    assert isinstance(data, dict)
    assert "files" in data
    assert isinstance(data["files"], list)

    # Verify file path format (should be "Folder/filename")
    for file_path in data["files"]:
        assert "/" in file_path, f"File path should contain '/': {file_path}"
        folder, filename = file_path.split("/", 1)
        assert folder in ["People", "Space"], f"Invalid folder: {folder}"
        assert len(filename) > 0, "Filename should not be empty"