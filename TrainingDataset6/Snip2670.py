def test_file_list_form_order(endpoint_path: str, tmp_file_1: Path, tmp_file_2: Path):
    response = client.post(
        url=endpoint_path,
        data={"city": "Thimphou"},
        files=(
            ("files", (tmp_file_1.name, tmp_file_1.read_bytes())),
            ("files", (tmp_file_2.name, tmp_file_2.read_bytes())),
        ),
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"file_contents": ["foo", "bar"], "city": "Thimphou"}