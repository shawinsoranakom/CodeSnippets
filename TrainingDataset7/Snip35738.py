def test_reverse_type_error_propagates(self):
        @DynamicConverter.register_to_url
        def raises_type_error(value):
            raise TypeError("This type error propagates.")

        with self.assertRaisesMessage(TypeError, "This type error propagates."):
            reverse("dynamic", kwargs={"value": object()})