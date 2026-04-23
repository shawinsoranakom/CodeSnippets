async def test_delete_api_key_route_unauthorized(client: AsyncClient, logged_in_headers, active_user):
    """Test that users cannot delete API keys belonging to other users."""
    # Import required modules
    from langflow.services.auth.utils import get_password_hash
    from langflow.services.database.models.user.model import User
    from langflow.services.deps import session_scope
    from sqlmodel import select

    # Create first user's API key
    basic_case = {
        "name": "test_key_user1",
        "total_uses": 0,
        "is_active": True,
        "api_key": "string",
        "user_id": str(active_user.id),
    }
    response = await client.post("api/v1/api_key/", json=basic_case, headers=logged_in_headers)
    assert response.status_code == status.HTTP_200_OK
    user1_api_key_id = response.json()["id"]

    # Create a second user and get their auth headers
    async with session_scope() as session:
        user2 = User(
            username="testuser2",
            password=get_password_hash("testpassword2"),
            is_active=True,
            is_superuser=False,
        )
        stmt = select(User).where(User.username == user2.username)
        existing_user = (await session.exec(stmt)).first()
        if not existing_user:
            session.add(user2)
            await session.flush()
            await session.refresh(user2)
        else:
            user2 = existing_user

    # Login as second user
    login_data = {"username": "testuser2", "password": "testpassword2"}
    response = await client.post("api/v1/login", data=login_data)
    assert response.status_code == status.HTTP_200_OK
    user2_token = response.json()["access_token"]
    user2_headers = {"Authorization": f"Bearer {user2_token}"}

    # Try to delete first user's API key using second user's credentials
    response = await client.delete(f"api/v1/api_key/{user1_api_key_id}", headers=user2_headers)

    # Should fail with 400 error (API Key not found - we don't reveal it exists)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "API Key not found" in response.json()["detail"]

    # Verify the first user's API key still exists by trying to delete it with correct credentials
    response = await client.delete(f"api/v1/api_key/{user1_api_key_id}", headers=logged_in_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["detail"] == "API Key deleted"

    # Clean up second user
    async with session_scope() as session:
        user = await session.get(User, user2.id)
        if user:
            await session.delete(user)