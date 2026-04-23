def test_function_registered_as_multiple_types() -> None:
    """Test that functions can be registered as multiple types simultaneously."""
    env = TemplateEnvironment(None)

    def multi_func(value: str = "default") -> str:
        return f"multi_{value}"

    extension = BaseTemplateExtension(
        env,
        functions=[
            TemplateFunction(
                "multi_func",
                multi_func,
                as_global=True,
                as_filter=True,
                as_test=True,
            ),
        ],
    )

    # Function should be registered in all three places
    assert "multi_func" in env.globals
    assert env.globals["multi_func"] is multi_func
    assert "multi_func" in env.filters
    assert env.filters["multi_func"] is multi_func
    assert "multi_func" in env.tests
    assert env.tests["multi_func"] is multi_func
    assert extension is not None