def test_propagates_pydantic2_model_config():
    app = FastAPI()

    class Missing:
        def __bool__(self):
            return False

    class EmbeddedModel(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)
        value: str | Missing = Missing()

    class Model(BaseModel):
        model_config = ConfigDict(
            arbitrary_types_allowed=True,
        )
        value: str | Missing = Missing()
        embedded_model: EmbeddedModel = EmbeddedModel()

    @app.post("/")
    def foo(req: Model) -> dict[str, str | None]:
        return {
            "value": req.value or None,
            "embedded_value": req.embedded_model.value or None,
        }

    client = TestClient(app)

    response = client.post("/", json={})
    assert response.status_code == 200, response.text
    assert response.json() == {
        "value": None,
        "embedded_value": None,
    }

    response2 = client.post(
        "/", json={"value": "foo", "embedded_model": {"value": "bar"}}
    )
    assert response2.status_code == 200, response2.text
    assert response2.json() == {
        "value": "foo",
        "embedded_value": "bar",
    }