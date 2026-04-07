def test_include_with_dollar(self):
        result = check_url_config(None)
        self.assertEqual(len(result), 1)
        warning = result[0]
        self.assertEqual(warning.id, "urls.W001")
        self.assertEqual(
            warning.msg,
            (
                "Your URL pattern '^include-with-dollar$' uses include with a "
                "route ending with a '$'. Remove the dollar from the route to "
                "avoid problems including URLs."
            ),
        )