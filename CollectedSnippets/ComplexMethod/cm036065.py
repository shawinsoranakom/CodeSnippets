def test_prepare_object_to_dump():
    str_obj = "str"
    assert prepare_object_to_dump(str_obj) == "'str'"

    list_obj = [1, 2, 3]
    assert prepare_object_to_dump(list_obj) == "[1, 2, 3]"

    dict_obj = {"a": 1, "b": "b"}
    assert prepare_object_to_dump(dict_obj) in [
        "{a: 1, b: 'b'}",
        "{b: 'b', a: 1}",
    ]

    set_obj = {1, 2, 3}
    assert prepare_object_to_dump(set_obj) == "[1, 2, 3]"

    tuple_obj = ("a", "b", "c")
    assert prepare_object_to_dump(tuple_obj) == "['a', 'b', 'c']"

    class CustomEnum(enum.Enum):
        A = enum.auto()
        B = enum.auto()
        C = enum.auto()

    assert prepare_object_to_dump(CustomEnum.A) == repr(CustomEnum.A)

    @dataclass
    class CustomClass:
        a: int
        b: str

    assert prepare_object_to_dump(CustomClass(1, "b")) == "CustomClass(a=1, b='b')"