def test_query_json_list():
    response = client.get(
        "/query-json-list", params={"items": json.dumps(["abc", "def"])}
    )
    assert response.status_code == 200, response.text
    assert response.json() == ["abc", "def"]