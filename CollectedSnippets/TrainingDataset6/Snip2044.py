def test_async_receiving_validated_pydantic_model(
    benchmark, client: TestClient
) -> None:
    status_code, body = _bench_post_json(
        benchmark, client, "/async/validated", json={"name": "foo", "value": 123}
    )
    assert status_code == 200
    assert body == b'{"name":"foo","value":123,"dep":42}'