def test_token_inactive_user(mod: ModuleType):
    client = TestClient(mod.app)
    alice_user_data = {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": mod.get_password_hash("secretalice"),
        "disabled": True,
    }
    with patch.dict(f"{mod.__name__}.fake_users_db", {"alice": alice_user_data}):
        access_token = get_access_token(
            username="alice", password="secretalice", client=client
        )
        response = client.get(
            "/users/me", headers={"Authorization": f"Bearer {access_token}"}
        )
    assert response.status_code == 400, response.text
    assert response.json() == {"detail": "Inactive user"}