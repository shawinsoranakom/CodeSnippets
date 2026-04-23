def test_resolve_value_error_means_no_match(self):
        @DynamicConverter.register_to_python
        def raises_value_error(value):
            raise ValueError()

        with self.assertRaises(Resolver404):
            resolve("/dynamic/abc/")