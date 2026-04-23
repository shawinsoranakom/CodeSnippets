def test_get_method_args_from_code(self, name, input, args, expected):
        """Parse method arguments from a string"""
        parsed = code_util.get_method_args_from_code(args, input)

        self.assertEqual(parsed, expected)