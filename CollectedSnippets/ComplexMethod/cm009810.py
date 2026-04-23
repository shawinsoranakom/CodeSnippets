def test_whole_class_inherited_beta() -> None:
    """Test whole class beta status for inherited class.

    The original version of beta decorator created duplicates with
    '.. beta::'.
    """

    # Test whole class beta status
    @beta()
    class BetaClass:
        @beta()
        def beta_method(self) -> str:
            """Original doc."""
            return "This is a beta method."

    @beta()
    class InheritedBetaClass(BetaClass):
        @beta()
        def beta_method(self) -> str:
            """Original doc."""
            return "This is a beta method 2."

    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter("always")

        obj = BetaClass()
        assert obj.beta_method() == "This is a beta method."

        assert len(warning_list) == 2
        warning = warning_list[0].message
        assert str(warning) == (
            "The class `test_whole_class_inherited_beta.<locals>.BetaClass` "
            "is in beta. It is actively being worked on, so the "
            "API may change."
        )

        warning = warning_list[1].message
        assert str(warning) == (
            "The method `test_whole_class_inherited_beta.<locals>.BetaClass."
            "beta_method` is in beta. It is actively being worked on, so "
            "the API may change."
        )

    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter("always")

        obj = InheritedBetaClass()
        assert obj.beta_method() == "This is a beta method 2."

        assert len(warning_list) == 2
        warning = warning_list[0].message
        assert str(warning) == (
            "The class `test_whole_class_inherited_beta.<locals>.InheritedBetaClass` "
            "is in beta. "
            "It is actively being worked on, so the "
            "API may change."
        )

        warning = warning_list[1].message
        assert str(warning) == (
            "The method `test_whole_class_inherited_beta.<locals>.InheritedBetaClass."
            "beta_method` is in beta. "
            "It is actively being worked on, so "
            "the API may change."
        )

        # if .. beta:: was inserted only once:
        if obj.__doc__ is not None:
            assert obj.__doc__.count(".. beta::") == 1