def test_async_return_large_dict_with_response_model(
    benchmark, client: TestClient
) -> None:
    status_code, body = _bench_get(
        benchmark, client, "/async/large-dict-with-response-model"
    )
    assert status_code == 200
    assert body == _expected_large_payload_json_bytes()