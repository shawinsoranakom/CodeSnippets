def test_stringified_annotations():
    app = FastAPI()

    client = TestClient(app)

    @app.get("/test/")
    def call(test: Annotated[str, Depends(Dep())]):
        return {"test": test}

    response = client.get("/test")
    assert response.status_code == 200