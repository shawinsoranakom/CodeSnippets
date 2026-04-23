def test_get_callable_parameters(self):
        self.assertIs(
            inspect._get_callable_parameters(Person.no_arguments),
            inspect._get_callable_parameters(Person.no_arguments),
        )
        self.assertIs(
            inspect._get_callable_parameters(Person().no_arguments),
            inspect._get_callable_parameters(Person().no_arguments),
        )