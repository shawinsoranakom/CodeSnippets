def test_func_supports_parameter(self):
        self.assertIs(
            inspect.func_supports_parameter(Person.all_kinds, "address"), True
        )
        self.assertIs(
            inspect.func_supports_parameter(Person().all_kinds, "address"),
            True,
        )
        self.assertIs(inspect.func_supports_parameter(Person.all_kinds, "zone"), False)
        self.assertIs(
            inspect.func_supports_parameter(Person().all_kinds, "zone"),
            False,
        )