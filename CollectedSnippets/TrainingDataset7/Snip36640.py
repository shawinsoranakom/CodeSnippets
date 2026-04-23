def test_mark_safe_as_decorator(self):
        """
        mark_safe used as a decorator leaves the result of a function
        unchanged.
        """

        def clean_string_provider():
            return "<html><body>dummy</body></html>"

        self.assertEqual(mark_safe(clean_string_provider)(), clean_string_provider())