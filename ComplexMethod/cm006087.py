async def test_profile_pictures_different_file_types(setup_profile_pictures, files_client):  # noqa: ARG001
    """Test that content-type headers are correct for SVG files.

    The real profile pictures are all SVG files. This test verifies
    that the content-type detection works correctly.

    Args:
        files_client: HTTP client for making API requests
        setup_profile_pictures: Fixture that sets up profile pictures directory
    """
    # Test SVG content type (all real profile pictures are SVGs)
    response = await files_client.get("api/v1/files/profile_pictures/Space/046-rocket.svg")
    assert response.status_code == 200
    assert "image/svg+xml" in response.headers["content-type"]

    # Test with a people profile picture
    list_response = await files_client.get("api/v1/files/profile_pictures/list")
    people_files = [f for f in list_response.json()["files"] if f.startswith("People/")]

    if people_files:
        first_people_file = people_files[0].replace("People/", "")
        response = await files_client.get(f"api/v1/files/profile_pictures/People/{first_people_file}")
        assert response.status_code == 200
        # All profile pictures should be SVGs
        assert "image/svg+xml" in response.headers["content-type"]