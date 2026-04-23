async def test_read_all_users_search(client: AsyncClient, logged_in_headers_super_user):
    """Test that the search parameter filters users by username across all pages."""
    # Create several users with distinct usernames
    usernames = ["alice_search", "bob_search", "charlie_search"]
    created_ids = []
    for username in usernames:
        response = await client.post(
            "api/v1/users/",
            json={"username": username, "password": "password123"},
            headers=logged_in_headers_super_user,
        )
        assert response.status_code == status.HTTP_201_CREATED
        created_ids.append(response.json()["id"])

    # Search for "alice" — should return exactly one match
    response = await client.get(
        "api/v1/users/?search=alice",
        headers=logged_in_headers_super_user,
    )
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert result["total_count"] == 1
    assert result["users"][0]["username"] == "alice_search"

    # Search for "_search" — should match all three created users
    response = await client.get(
        "api/v1/users/?search=_search",
        headers=logged_in_headers_super_user,
    )
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert result["total_count"] == 3
    returned_usernames = {u["username"] for u in result["users"]}
    assert returned_usernames == set(usernames)

    # Search for a non-existent username — should return zero results
    response = await client.get(
        "api/v1/users/?search=nonexistentuser",
        headers=logged_in_headers_super_user,
    )
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert result["total_count"] == 0
    assert result["users"] == []

    # Search is case-insensitive
    response = await client.get(
        "api/v1/users/?search=ALICE",
        headers=logged_in_headers_super_user,
    )
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert result["total_count"] == 1
    assert result["users"][0]["username"] == "alice_search"

    # Search combined with pagination: limit=1 should return 1 user but total_count=3
    response = await client.get(
        "api/v1/users/?search=_search&limit=1",
        headers=logged_in_headers_super_user,
    )
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert result["total_count"] == 3
    assert len(result["users"]) == 1

    # Clean up
    for user_id in created_ids:
        await client.delete(f"api/v1/users/{user_id}", headers=logged_in_headers_super_user)