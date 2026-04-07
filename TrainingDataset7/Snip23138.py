def test_simplest_class(self):
        @html_safe
        class SimpleJS:
            """The simplest possible asset class."""

            def __str__(self):
                return '<script src="https://example.org/asset.js" rel="stylesheet">'

        m = Media(js=(SimpleJS(),))
        self.assertEqual(
            str(m),
            '<script src="https://example.org/asset.js" rel="stylesheet">',
        )