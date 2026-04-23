def test_resume_from_last_item(client: TestClient):
    response = client.get(
        "/items/stream",
        headers={"last-event-id": "1"},
    )
    assert response.status_code == 200, response.text

    data_lines = [
        line for line in response.text.strip().split("\n") if line.startswith("data: ")
    ]
    assert len(data_lines) == 1

    id_lines = [
        line for line in response.text.strip().split("\n") if line.startswith("id: ")
    ]
    assert id_lines == ["id: 2"]