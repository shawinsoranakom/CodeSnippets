def test_read_items(mod: ModuleType):
    client = TestClient(mod.app)
    access_token = get_access_token(client=client)
    response = client.get(
        "/users/me/items/", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200, response.text
    assert response.json() == [{"item_id": "Foo", "owner": "johndoe"}]