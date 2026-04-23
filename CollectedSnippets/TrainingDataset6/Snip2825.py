def test_cookie_json_list():
    client.cookies.set("items", json.dumps(["abc", "def"]))
    response = client.get("/cookie-json-list")
    assert response.status_code == 200, response.text
    assert response.json() == ["abc", "def"]
    client.cookies.clear()