def test_sync_return_large_dict_without_response_model(
    benchmark, client: TestClient
) -> None:
    status_code, body = _bench_get(
        benchmark, client, "/sync/large-dict-no-response-model"
    )
    assert status_code == 200
    assert body == _expected_large_payload_json_bytes()