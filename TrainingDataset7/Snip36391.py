def test_strip_spaces_between_tags(self):
        # Strings that should come out untouched.
        items = (" <adf>", "<adf> ", " </adf> ", " <f> x</f>")
        for value in items:
            with self.subTest(value=value):
                self.check_output(strip_spaces_between_tags, value)
                self.check_output(strip_spaces_between_tags, lazystr(value))

        # Strings that have spaces to strip.
        items = (
            ("<d> </d>", "<d></d>"),
            ("<p>hello </p>\n<p> world</p>", "<p>hello </p><p> world</p>"),
            ("\n<p>\t</p>\n<p> </p>\n", "\n<p></p><p></p>\n"),
        )
        for value, output in items:
            with self.subTest(value=value, output=output):
                self.check_output(strip_spaces_between_tags, value, output)
                self.check_output(strip_spaces_between_tags, lazystr(value), output)