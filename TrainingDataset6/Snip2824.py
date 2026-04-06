def test_header_json_list():
    response = client.get(
        "/header-json-list", headers={"x-items": json.dumps(["abc", "def"])}
    )
    assert response.status_code == 200, response.text
    assert response.json() == ["abc", "def"]