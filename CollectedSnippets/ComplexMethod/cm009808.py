def test_rename_parameter() -> None:
    """Test rename parameter."""

    @rename_parameter(since="2.0.0", removal="3.0.0", old="old_name", new="new_name")
    def foo(new_name: str) -> str:
        """Original doc."""
        return new_name

    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter("always")
        assert foo(old_name="hello") == "hello"  # type: ignore[call-arg]
        assert len(warning_list) == 1

        assert foo(new_name="hello") == "hello"
        assert foo("hello") == "hello"
        assert foo.__doc__ == "Original doc."
        with pytest.raises(TypeError):
            foo(meow="hello")  # type: ignore[call-arg]
        with pytest.raises(TypeError):
            assert foo("hello", old_name="hello")  # type: ignore[call-arg]

        with pytest.raises(TypeError):
            assert foo(old_name="goodbye", new_name="hello")