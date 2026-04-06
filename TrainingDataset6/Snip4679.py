def test_get_db(module: ModuleType):
    app = FastAPI()

    @app.get("/")
    def read_root(c: Annotated[Any, Depends(module.dependency_c)]):
        return {"c": str(c)}

    client = TestClient(app)

    a_mock = Mock()
    b_mock = Mock()
    c_mock = Mock()

    with (
        patch(
            f"{module.__name__}.generate_dep_a",
            return_value=a_mock,
            create=True,
        ),
        patch(
            f"{module.__name__}.generate_dep_b",
            return_value=b_mock,
            create=True,
        ),
        patch(
            f"{module.__name__}.generate_dep_c",
            return_value=c_mock,
            create=True,
        ),
    ):
        response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"c": str(c_mock)}