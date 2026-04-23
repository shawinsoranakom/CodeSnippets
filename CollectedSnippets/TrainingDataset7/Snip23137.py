def test_construction(self):
        m = Media(
            css={
                "all": (
                    CSS("path/to/css1", media="all"),
                    CSS("/path/to/css2", media="all"),
                )
            },
            js=(
                Script("/path/to/js1"),
                Script("http://media.other.com/path/to/js2"),
                Script(
                    "https://secure.other.com/path/to/js3",
                    integrity="9d947b87fdeb25030d56d01f7aa75800",
                ),
            ),
        )
        self.assertHTMLEqual(
            str(m),
            '<link href="http://media.example.com/static/path/to/css1" media="all" '
            'rel="stylesheet">\n'
            '<link href="/path/to/css2" media="all" rel="stylesheet">\n'
            '<script src="/path/to/js1"></script>\n'
            '<script src="http://media.other.com/path/to/js2"></script>\n'
            '<script src="https://secure.other.com/path/to/js3" '
            'integrity="9d947b87fdeb25030d56d01f7aa75800"></script>',
        )
        self.assertEqual(
            repr(m),
            "Media(css={'all': [CSS('path/to/css1'), CSS('/path/to/css2')]}, "
            "js=[Script('/path/to/js1'), Script('http://media.other.com/path/to/js2'), "
            "Script('https://secure.other.com/path/to/js3')])",
        )