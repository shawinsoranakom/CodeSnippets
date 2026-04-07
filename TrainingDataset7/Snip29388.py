def check_attribute(self, name, paginator, expected, params, coerce=None):
        """
        Helper method that checks a single attribute and gives a nice error
        message upon test failure.
        """
        got = getattr(paginator, name)
        if coerce is not None:
            got = coerce(got)
        self.assertEqual(
            expected,
            got,
            "For '%s', expected %s but got %s. Paginator parameters were: %s"
            % (name, expected, got, params),
        )