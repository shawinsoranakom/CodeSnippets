def test_stream_all_items(client: TestClient):
    response = client.get("/items/stream")
    assert response.status_code == 200, response.text

    data_lines = [
        line for line in response.text.strip().split("\n") if line.startswith("data: ")
    ]
    assert len(data_lines) == 3

    id_lines = [
        line for line in response.text.strip().split("\n") if line.startswith("id: ")
    ]
    assert id_lines == ["id: 0", "id: 1", "id: 2"]