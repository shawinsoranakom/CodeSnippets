def test_stream_story(client: TestClient, path: str):
    response = client.get(path)
    assert response.status_code == 200, response.text
    assert response.text == expected_text