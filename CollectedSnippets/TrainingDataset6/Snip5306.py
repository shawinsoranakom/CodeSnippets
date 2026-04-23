def test_stream_image(mod, client: TestClient, path: str):
    response = client.get(path)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content == mod.binary_image