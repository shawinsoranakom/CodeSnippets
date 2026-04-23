def test_sync_return_model_with_response_model(benchmark, client: TestClient) -> None:
    status_code, body = _bench_get(benchmark, client, "/sync/model-with-response-model")
    assert status_code == 200
    assert body == b'{"name":"foo","value":123,"dep":42}'