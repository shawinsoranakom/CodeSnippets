def test_stylesheets(self):
        testdata = [
            # Plain strings.
            ("/test.xsl", 'href="/test.xsl" media="screen" type="text/xsl"'),
            ("/test.xslt", 'href="/test.xslt" media="screen" type="text/xsl"'),
            ("/test.css", 'href="/test.css" media="screen" type="text/css"'),
            ("/test", 'href="/test" media="screen"'),
            (
                "https://example.com/test.xsl",
                'href="https://example.com/test.xsl" media="screen" type="text/xsl"',
            ),
            (
                "https://example.com/test.css",
                'href="https://example.com/test.css" media="screen" type="text/css"',
            ),
            (
                "https://example.com/test",
                'href="https://example.com/test" media="screen"',
            ),
            ("/♥.xsl", 'href="/%E2%99%A5.xsl" media="screen" type="text/xsl"'),
            (
                static("stylesheet.xsl"),
                'href="/static/stylesheet.xsl" media="screen" type="text/xsl"',
            ),
            (
                static("stylesheet.css"),
                'href="/static/stylesheet.css" media="screen" type="text/css"',
            ),
            (static("stylesheet"), 'href="/static/stylesheet" media="screen"'),
            (
                reverse("syndication-xsl-stylesheet"),
                'href="/syndication/stylesheet.xsl" media="screen" type="text/xsl"',
            ),
            (
                reverse_lazy("syndication-xsl-stylesheet"),
                'href="/syndication/stylesheet.xsl" media="screen" type="text/xsl"',
            ),
            # Stylesheet objects.
            (
                Stylesheet("/test.xsl"),
                'href="/test.xsl" media="screen" type="text/xsl"',
            ),
            (Stylesheet("/test.xsl", mimetype=None), 'href="/test.xsl" media="screen"'),
            (Stylesheet("/test.xsl", media=None), 'href="/test.xsl" type="text/xsl"'),
            (Stylesheet("/test.xsl", mimetype=None, media=None), 'href="/test.xsl"'),
            (
                Stylesheet("/test.xsl", mimetype="text/xml"),
                'href="/test.xsl" media="screen" type="text/xml"',
            ),
        ]
        for stylesheet, expected in testdata:
            feed = Rss201rev2Feed(
                title="test",
                link="https://example.com",
                description="test",
                stylesheets=[stylesheet],
            )
            doc = feed.writeString("utf-8")
            with self.subTest(expected=expected):
                self.assertIn(f"<?xml-stylesheet {expected}?>", doc)