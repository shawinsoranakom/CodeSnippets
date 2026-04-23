def test_sync_receiving_large_payload(benchmark, client: TestClient) -> None:
    status_code, body = _bench_post_json(
        benchmark,
        client,
        "/sync/large-receive",
        json=LARGE_PAYLOAD,
    )
    assert status_code == 200
    assert body == b'{"received":300}'