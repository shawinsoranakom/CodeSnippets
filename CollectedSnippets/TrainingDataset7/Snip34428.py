def test_filter_deferred_annotation(self):
        register = Library()

        @register.filter("example")
        def example_filter(value: str, arg: SomeType):  # NOQA: F821
            return f"{value}_{arg}"

        result = FilterExpression.args_check(
            "example", example_filter, ["extra_example"]
        )

        self.assertIs(result, True)