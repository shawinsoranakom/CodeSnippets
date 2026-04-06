def test_regular_no_stream():
    response = client.get("/data")
    assert response.json() == ["foo", "bar", "baz"]