def test__get_all_basemodel_annotations_v2(*, use_v1_namespace: bool) -> None:
    A = TypeVar("A")

    if use_v1_namespace:
        if sys.version_info >= (3, 14):
            pytest.skip("pydantic.v1 namespace not supported with Python 3.14+")

        class ModelA(BaseModelV1, Generic[A], extra="allow"):
            a: A

        class EmptyModel(BaseModelV1, Generic[A], extra="allow"):
            pass

    else:

        class ModelA(BaseModel, Generic[A]):  # type: ignore[no-redef]
            a: A
            model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

        class EmptyModel(BaseModel, Generic[A]):  # type: ignore[no-redef]
            model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    class ModelB(ModelA[str]):
        b: Annotated[ModelA[dict[str, Any]], "foo"]

    class Mixin:
        def foo(self) -> str:
            return "foo"

    class ModelC(Mixin, ModelB):
        c: dict

    expected = {"a": str, "b": Annotated[ModelA[dict[str, Any]], "foo"], "c": dict}
    actual = get_all_basemodel_annotations(ModelC)
    assert actual == expected

    expected = {"a": str, "b": Annotated[ModelA[dict[str, Any]], "foo"]}
    actual = get_all_basemodel_annotations(ModelB)
    assert actual == expected

    expected = {"a": Any}
    actual = get_all_basemodel_annotations(ModelA)
    assert actual == expected

    expected = {"a": int}
    actual = get_all_basemodel_annotations(ModelA[int])
    assert actual == expected

    D = TypeVar("D", bound=str | int)

    class ModelD(ModelC, Generic[D]):
        d: D | None

    expected = {
        "a": str,
        "b": Annotated[ModelA[dict[str, Any]], "foo"],
        "c": dict,
        "d": str | int | None,
    }
    actual = get_all_basemodel_annotations(ModelD)
    assert actual == expected

    expected = {
        "a": str,
        "b": Annotated[ModelA[dict[str, Any]], "foo"],
        "c": dict,
        "d": int | None,
    }
    actual = get_all_basemodel_annotations(ModelD[int])
    assert actual == expected

    expected = {}
    actual = get_all_basemodel_annotations(EmptyModel)
    assert actual == expected