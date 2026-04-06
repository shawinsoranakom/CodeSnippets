def test_post_file_no_token(tmp_path, app: FastAPI):
    path = tmp_path / "test.txt"
    path.write_bytes(b"<file content>")

    client = TestClient(app)
    with path.open("rb") as file:
        response = client.post("/files/", files={"file": file})
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["body", "fileb"],
                "msg": "Field required",
                "input": None,
            },
            {
                "type": "missing",
                "loc": ["body", "token"],
                "msg": "Field required",
                "input": None,
            },
        ]
    }