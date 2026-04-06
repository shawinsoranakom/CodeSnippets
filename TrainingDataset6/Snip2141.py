def test_multiple_annotations():
    async def dep():
        pass  # pragma: nocover

    @app.get("/multi-query")
    async def get(foo: Annotated[int, Query(gt=2), Query(lt=10)]):
        return foo

    with pytest.raises(
        AssertionError,
        match=(
            "Cannot specify `Depends` in `Annotated` and default value"
            " together for 'foo'"
        ),
    ):

        @app.get("/")
        async def get2(foo: Annotated[int, Depends(dep)] = Depends(dep)):
            pass  # pragma: nocover

    with pytest.raises(
        AssertionError,
        match=(
            "Cannot specify a FastAPI annotation in `Annotated` and `Depends` as a"
            " default value together for 'foo'"
        ),
    ):

        @app.get("/")
        async def get3(foo: Annotated[int, Query(min_length=1)] = Depends(dep)):
            pass  # pragma: nocover

    client = TestClient(app)
    response = client.get("/multi-query", params={"foo": "5"})
    assert response.status_code == 200
    assert response.json() == 5

    response = client.get("/multi-query", params={"foo": "123"})
    assert response.status_code == 422

    response = client.get("/multi-query", params={"foo": "1"})
    assert response.status_code == 422