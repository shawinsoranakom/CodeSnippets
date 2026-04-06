def test_typeadapter():
    # This test is only to confirm that Pydantic alone is working as expected
    from pydantic import (
        BaseModel,
        ConfigDict,
        PlainSerializer,
        TypeAdapter,
        WithJsonSchema,
    )

    class FakeNumpyArray:
        def __init__(self):
            self.data = [1.0, 2.0, 3.0]

    FakeNumpyArrayPydantic = Annotated[
        FakeNumpyArray,
        WithJsonSchema(TypeAdapter(list[float]).json_schema()),
        PlainSerializer(lambda v: v.data),
    ]

    class MyModel(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)
        custom_field: FakeNumpyArrayPydantic

    ta = TypeAdapter(MyModel)
    assert ta.dump_python(MyModel(custom_field=FakeNumpyArray())) == {
        "custom_field": [1.0, 2.0, 3.0]
    }
    assert ta.json_schema() == snapshot(
        {
            "properties": {
                "custom_field": {
                    "items": {"type": "number"},
                    "title": "Custom Field",
                    "type": "array",
                }
            },
            "required": ["custom_field"],
            "title": "MyModel",
            "type": "object",
        }
    )