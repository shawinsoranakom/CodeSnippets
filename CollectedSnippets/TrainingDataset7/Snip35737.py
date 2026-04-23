def test_reverse_value_error_means_no_match(self):
        @DynamicConverter.register_to_url
        def raises_value_error(value):
            raise ValueError

        with self.assertRaises(NoReverseMatch):
            reverse("dynamic", kwargs={"value": object()})