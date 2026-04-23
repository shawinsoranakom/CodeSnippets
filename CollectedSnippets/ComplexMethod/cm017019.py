def test_async_generator_with_model(client: TestClient):
    response = client.get("/items/stream")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    assert response.headers["cache-control"] == "no-cache"
    assert response.headers["x-accel-buffering"] == "no"

    lines = response.text.strip().split("\n")
    data_lines = [line for line in lines if line.startswith("data: ")]
    assert len(data_lines) == 3
    assert '"name":"Plumbus"' in data_lines[0] or '"name": "Plumbus"' in data_lines[0]
    assert (
        '"name":"Portal Gun"' in data_lines[1]
        or '"name": "Portal Gun"' in data_lines[1]
    )
    assert (
        '"name":"Meeseeks Box"' in data_lines[2]
        or '"name": "Meeseeks Box"' in data_lines[2]
    )