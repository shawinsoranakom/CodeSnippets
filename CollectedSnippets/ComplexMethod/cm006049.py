async def test_patch_user(client: AsyncClient, logged_in_headers_super_user):
    name = "string"
    updated_name = "string2"
    basic_case = {"username": name, "password": "string"}
    response_ = await client.post("api/v1/users/", json=basic_case, headers=logged_in_headers_super_user)
    id_ = response_.json()["id"]
    basic_case["username"] = updated_name
    response = await client.patch(f"api/v1/users/{id_}", json=basic_case, headers=logged_in_headers_super_user)
    result = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(result, dict), "The result must be a dictionary"
    assert "id" in result, "The result must have an 'id' key"
    assert "is_active" in result, "The result must have an 'is_active' key"
    assert "is_superuser" in result, "The result must have an 'is_superuser' key"
    assert "last_login_at" in result, "The result must have an 'last_login_at' key"
    assert "profile_image" in result, "The result must have an 'profile_image' key"
    assert "store_api_key" in result, "The result must have an 'store_api_key' key"
    assert "updated_at" in result, "The result must have an 'updated_at' key"
    assert "username" in result, "The result must have an 'username' key"
    assert result["username"] == updated_name, "The username must be updated"