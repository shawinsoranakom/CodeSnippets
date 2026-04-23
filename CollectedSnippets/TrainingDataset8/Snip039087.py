def test_failed_get_args_from_code(self, name, input, args, expected):
        """Fail to parse method arguments from a string

        The inclusion of `,` or `)` in a string with multiple args causes error
        """
        with self.assertRaises(AssertionError):
            code_util.get_method_args_from_code(args, input)