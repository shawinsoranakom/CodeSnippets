def test_resolve_type_error_propagates(self):
        @DynamicConverter.register_to_python
        def raises_type_error(value):
            raise TypeError("This type error propagates.")

        with self.assertRaisesMessage(TypeError, "This type error propagates."):
            resolve("/dynamic/abc/")