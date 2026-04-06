def _bench_get(benchmark, client: TestClient, path: str) -> tuple[int, bytes]:
    warmup = client.get(path)
    assert warmup.status_code == 200

    def do_request() -> tuple[int, bytes]:
        response = client.get(path)
        return response.status_code, response.content

    return benchmark(do_request)