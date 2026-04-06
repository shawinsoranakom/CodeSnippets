def _bench_post_json(
    benchmark, client: TestClient, path: str, json: dict[str, Any]
) -> tuple[int, bytes]:
    warmup = client.post(path, json=json)
    assert warmup.status_code == 200

    def do_request() -> tuple[int, bytes]:
        response = client.post(path, json=json)
        return response.status_code, response.content

    return benchmark(do_request)