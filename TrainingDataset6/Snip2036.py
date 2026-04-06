def client() -> Iterator[TestClient]:
    with TestClient(app) as client:
        yield client