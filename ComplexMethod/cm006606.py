def test_post_process_type_function(self):
        # Basic types
        assert set(post_process_type(int)) == {int}
        assert set(post_process_type(float)) == {float}

        # List and Sequence types
        assert set(post_process_type(list[int])) == {int}
        assert set(post_process_type(SequenceABC[float])) == {float}

        # Union types
        assert set(post_process_type(Union[int, str])) == {int, str}  # noqa: UP007
        assert set(post_process_type(Union[int, SequenceABC[str]])) == {int, str}  # noqa: UP007
        assert set(post_process_type(Union[int, SequenceABC[int]])) == {int}  # noqa: UP007

        # Nested Union with lists
        assert set(post_process_type(Union[list[int], list[str]])) == {int, str}  # noqa: UP007
        assert set(post_process_type(Union[int, list[str], list[float]])) == {int, str, float}  # noqa: UP007

        # Custom data types
        assert set(post_process_type(Data)) == {Data}
        assert set(post_process_type(list[Data])) == {Data}

        # Union with custom types
        assert set(post_process_type(Union[Data, str])) == {Data, str}  # noqa: UP007
        assert set(post_process_type(Union[Data, int, list[str]])) == {Data, int, str}  # noqa: UP007

        # Empty lists and edge cases
        assert set(post_process_type(list)) == {list}
        assert set(post_process_type(Union[int, None])) == {int, NoneType}  # noqa: UP007
        assert set(post_process_type(Union[list[None], None])) == {None, NoneType}  # noqa: UP007

        # Handling complex nested structures
        assert set(post_process_type(Union[SequenceABC[int | str], list[float]])) == {int, str, float}  # noqa: UP007
        assert set(post_process_type(Union[int | list[str] | list[float], str])) == {int, str, float}  # noqa: UP007

        # Non-generic types should return as is
        assert set(post_process_type(dict)) == {dict}
        assert set(post_process_type(tuple)) == {tuple}

        # Union with custom types
        assert set(post_process_type(Union[Data, str])) == {Data, str}  # noqa: UP007
        assert set(post_process_type(Data | str)) == {Data, str}
        assert set(post_process_type(Data | int | list[str])) == {Data, int, str}

        # More complex combinations with Data
        assert set(post_process_type(Data | list[float])) == {Data, float}
        assert set(post_process_type(Data | Union[int, str])) == {Data, int, str}  # noqa: UP007
        assert set(post_process_type(Data | list[int] | None)) == {Data, int, type(None)}
        assert set(post_process_type(Data | Union[float, None])) == {Data, float, type(None)}  # noqa: UP007

        # Multiple Data types combined
        assert set(post_process_type(Union[Data, str | float])) == {Data, str, float}  # noqa: UP007
        assert set(post_process_type(Union[Data | float | str, int])) == {Data, int, float, str}  # noqa: UP007

        # Testing with nested unions and lists
        assert set(post_process_type(Union[list[Data], list[int | str]])) == {Data, int, str}  # noqa: UP007
        assert set(post_process_type(Data | list[float | str])) == {Data, float, str}