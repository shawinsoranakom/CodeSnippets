def test_stylesheets_repr(self):
        testdata = [
            (Stylesheet("/test.xsl", mimetype=None), "('/test.xsl', None, 'screen')"),
            (Stylesheet("/test.xsl", media=None), "('/test.xsl', 'text/xsl', None)"),
            (
                Stylesheet("/test.xsl", mimetype=None, media=None),
                "('/test.xsl', None, None)",
            ),
            (
                Stylesheet("/test.xsl", mimetype="text/xml"),
                "('/test.xsl', 'text/xml', 'screen')",
            ),
        ]
        for stylesheet, expected in testdata:
            self.assertEqual(repr(stylesheet), expected)