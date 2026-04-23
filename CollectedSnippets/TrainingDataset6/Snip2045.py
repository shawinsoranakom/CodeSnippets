def test_async_return_dict_without_response_model(
    benchmark, client: TestClient
) -> None:
    status_code, body = _bench_get(benchmark, client, "/async/dict-no-response-model")
    assert status_code == 200
    assert body == b'{"name":"foo","value":123}'