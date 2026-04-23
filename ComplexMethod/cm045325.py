def test_nested_data_model() -> None:
    class MyBaseModel(BaseModel):
        message: str

    @dataclass
    class NestedBaseModel:
        nested: MyBaseModel

    @dataclass
    class NestedBaseModelList:
        nested: List[MyBaseModel]

    @dataclass
    class NestedBaseModelList2:
        nested: List[MyBaseModel]

    @dataclass
    class NestedBaseModelList3:
        nested: List[List[MyBaseModel]]

    @dataclass
    class NestedBaseModelList4:
        nested: List[List[List[List[List[List[MyBaseModel]]]]]]

    @dataclass
    class NestedBaseModelUnion:
        nested: Union[MyBaseModel, str]

    @dataclass
    class NestedBaseModelUnion2:
        nested: MyBaseModel | str

    assert has_nested_base_model(NestedBaseModel)
    assert has_nested_base_model(NestedBaseModelList)
    assert has_nested_base_model(NestedBaseModelList2)
    assert has_nested_base_model(NestedBaseModelList3)
    assert has_nested_base_model(NestedBaseModelList4)
    assert has_nested_base_model(NestedBaseModelUnion)
    assert has_nested_base_model(NestedBaseModelUnion2)