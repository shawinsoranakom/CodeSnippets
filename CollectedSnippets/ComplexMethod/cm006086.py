async def test_download_profile_picture_people(setup_profile_pictures, files_client):  # noqa: ARG001
    """Test downloading a profile picture from People folder.

    Note: The actual people profile pictures are copied during app init,
    so we test with whatever profile picture exists.

    Args:
        files_client: HTTP client for making API requests
        setup_profile_pictures: Fixture that sets up profile pictures directory
    """
    # List available people profile pictures first
    list_response = await files_client.get("api/v1/files/profile_pictures/list")
    assert list_response.status_code == 200
    people_files = [f for f in list_response.json()["files"] if f.startswith("People/")]

    # Skip test if no people profile pictures are available
    if not people_files:
        import pytest

        pytest.skip("No people profile pictures available")

    # Test downloading the first available people profile picture
    first_people_file = people_files[0].replace("People/", "")
    response = await files_client.get(f"api/v1/files/profile_pictures/People/{first_people_file}")
    assert response.status_code == 200

    # Verify content type
    assert "image/svg+xml" in response.headers["content-type"]

    # Verify content
    content = response.content
    assert b"<svg" in content
    assert b"</svg>" in content
    assert len(content) > 100, "SVG content should be substantial"