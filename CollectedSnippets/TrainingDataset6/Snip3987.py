def get_client():
    app = FastAPI()

    class ModelWithRef(BaseModel):
        ref: str = Field(validation_alias="$ref", serialization_alias="$ref")
        model_config = ConfigDict(validate_by_alias=True, serialize_by_alias=True)

    @app.get("/", response_model=ModelWithRef)
    async def read_root() -> Any:
        return {"$ref": "some-ref"}

    client = TestClient(app)
    return client