def test_resume_from_last_event_id(client: TestClient):
    response = client.get(
        "/items/stream",
        headers={"last-event-id": "0"},
    )
    assert response.status_code == 200, response.text

    data_lines = [
        line for line in response.text.strip().split("\n") if line.startswith("data: ")
    ]
    assert len(data_lines) == 2

    id_lines = [
        line for line in response.text.strip().split("\n") if line.startswith("id: ")
    ]
    assert id_lines == ["id: 1", "id: 2"]