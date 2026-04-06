def test_file_form_order(endpoint_path: str, tmp_file_1: Path):
    response = client.post(
        url=endpoint_path,
        data={"city": "Thimphou"},
        files={"file": (tmp_file_1.name, tmp_file_1.read_bytes())},
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"file_content": "foo", "city": "Thimphou"}