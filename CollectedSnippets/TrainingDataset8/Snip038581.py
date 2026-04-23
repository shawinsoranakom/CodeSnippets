def test_param_names_are_camel_case(self):
        """Test that param names must be camelCase.

        Note the exception is the "_test" section which is used
        for unit testing.
        """
        with self.assertRaises(AssertionError):
            config._create_option("_test.snake_case")