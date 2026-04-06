def test_form_json_list():
    response = client.post(
        "/form-json-list", data={"items": json.dumps(["abc", "def"])}
    )
    assert response.status_code == 200, response.text
    assert response.json() == ["abc", "def"]