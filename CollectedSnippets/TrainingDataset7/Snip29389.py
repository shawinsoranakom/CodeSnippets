async def check_attribute_async(self, name, paginator, expected, params):
        """See check_attribute."""
        got = getattr(paginator, name)
        self.assertEqual(
            expected,
            await got(),
            "For '%s', expected %s but got %s. Paginator parameters were: %s"
            % (name, expected, got, params),
        )