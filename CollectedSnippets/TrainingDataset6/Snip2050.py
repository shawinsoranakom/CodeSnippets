def test_async_receiving_large_payload(benchmark, client: TestClient) -> None:
    status_code, body = _bench_post_json(
        benchmark,
        client,
        "/async/large-receive",
        json=LARGE_PAYLOAD,
    )
    assert status_code == 200
    assert body == b'{"received":300}'