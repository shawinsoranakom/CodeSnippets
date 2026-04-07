def test_construction(self):
        # Check construction of media objects
        m = Media(
            css={"all": ("path/to/css1", "/path/to/css2")},
            js=(
                "/path/to/js1",
                "http://media.other.com/path/to/js2",
                "https://secure.other.com/path/to/js3",
            ),
        )
        self.assertEqual(
            str(m),
            '<link href="http://media.example.com/static/path/to/css1" media="all" '
            'rel="stylesheet">\n'
            '<link href="/path/to/css2" media="all" rel="stylesheet">\n'
            '<script src="/path/to/js1"></script>\n'
            '<script src="http://media.other.com/path/to/js2"></script>\n'
            '<script src="https://secure.other.com/path/to/js3"></script>',
        )
        self.assertEqual(
            repr(m),
            "Media(css={'all': ['path/to/css1', '/path/to/css2']}, "
            "js=['/path/to/js1', 'http://media.other.com/path/to/js2', "
            "'https://secure.other.com/path/to/js3'])",
        )

        class Foo:
            css = {"all": ("path/to/css1", "/path/to/css2")}
            js = (
                "/path/to/js1",
                "http://media.other.com/path/to/js2",
                "https://secure.other.com/path/to/js3",
            )

        m3 = Media(Foo)
        self.assertEqual(
            str(m3),
            '<link href="http://media.example.com/static/path/to/css1" media="all" '
            'rel="stylesheet">\n'
            '<link href="/path/to/css2" media="all" rel="stylesheet">\n'
            '<script src="/path/to/js1"></script>\n'
            '<script src="http://media.other.com/path/to/js2"></script>\n'
            '<script src="https://secure.other.com/path/to/js3"></script>',
        )

        # A widget can exist without a media definition
        class MyWidget(TextInput):
            pass

        w = MyWidget()
        self.assertEqual(str(w.media), "")