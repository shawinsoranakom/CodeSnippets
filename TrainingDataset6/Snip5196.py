def get_access_token(*, username="johndoe", password="secret", client: TestClient):
    data = {"username": username, "password": password}
    response = client.post("/token", data=data)
    content = response.json()
    access_token = content.get("access_token")
    return access_token