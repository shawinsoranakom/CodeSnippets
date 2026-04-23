def test_whole_class_inherited_deprecation() -> None:
    """Test whole class deprecation for inherited class.

    The original version of deprecation decorator created duplicates with
    '[*Deprecated*]'.
    """

    # Test whole class deprecation
    @deprecated(since="2.0.0", removal="3.0.0")
    class DeprecatedClass:
        def __init__(self) -> None:
            """Original doc."""

        @deprecated(since="2.0.0", removal="3.0.0")
        def deprecated_method(self) -> str:
            """Original doc."""
            return "This is a deprecated method."

    @deprecated(since="2.2.0", removal="3.2.0")
    class InheritedDeprecatedClass(DeprecatedClass):
        """Inherited deprecated class."""

        def __init__(self) -> None:
            """Original doc."""

        @deprecated(since="2.2.0", removal="3.2.0")
        def deprecated_method(self) -> str:
            """Original doc."""
            return "This is a deprecated method."

    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter("always")

        obj = DeprecatedClass()
        assert obj.deprecated_method() == "This is a deprecated method."

        assert len(warning_list) == 2
        warning = warning_list[0].message
        assert str(warning) == (
            "The class `test_whole_class_inherited_deprecation.<locals>."
            "DeprecatedClass` was "
            "deprecated in tests 2.0.0 and will be removed in 3.0.0"
        )

        warning = warning_list[1].message
        assert str(warning) == (
            "The method `test_whole_class_inherited_deprecation.<locals>."
            "DeprecatedClass.deprecated_method` was deprecated in "
            "tests 2.0.0 and will be removed in 3.0.0"
        )
        # if [*Deprecated*] was inserted only once:
        if obj.__doc__ is not None:
            assert obj.__doc__.count("!!! deprecated") == 1

    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter("always")

        obj = InheritedDeprecatedClass()
        assert obj.deprecated_method() == "This is a deprecated method."

        assert len(warning_list) == 2
        warning = warning_list[0].message
        assert str(warning) == (
            "The class "
            "`test_whole_class_inherited_deprecation.<locals>.InheritedDeprecatedClass`"
            " was deprecated in tests 2.2.0 and will be removed in 3.2.0"
        )

        warning = warning_list[1].message
        assert str(warning) == (
            "The method `test_whole_class_inherited_deprecation.<locals>."
            "InheritedDeprecatedClass.deprecated_method` was deprecated in "
            "tests 2.2.0 and will be removed in 3.2.0"
        )
        # if [*Deprecated*] was inserted only once:
        if obj.__doc__ is not None:
            assert obj.__doc__.count("!!! deprecated") == 1
            assert "!!! deprecated" in obj.__doc__