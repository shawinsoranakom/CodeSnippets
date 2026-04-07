def test_media_dsl(self):
        ###############################################################
        # DSL Class-based media definitions
        ###############################################################

        # A widget can define media if it needs to.
        # Any absolute path will be preserved; relative paths are combined
        # with the value of settings.MEDIA_URL
        class MyWidget1(TextInput):
            class Media:
                css = {"all": ("path/to/css1", "/path/to/css2")}
                js = (
                    "/path/to/js1",
                    "http://media.other.com/path/to/js2",
                    "https://secure.other.com/path/to/js3",
                )

        w1 = MyWidget1()
        self.assertEqual(
            str(w1.media),
            '<link href="http://media.example.com/static/path/to/css1" media="all" '
            'rel="stylesheet">\n'
            '<link href="/path/to/css2" media="all" rel="stylesheet">\n'
            '<script src="/path/to/js1"></script>\n'
            '<script src="http://media.other.com/path/to/js2"></script>\n'
            '<script src="https://secure.other.com/path/to/js3"></script>',
        )

        # Media objects can be interrogated by media type
        self.assertEqual(
            str(w1.media["css"]),
            '<link href="http://media.example.com/static/path/to/css1" media="all" '
            'rel="stylesheet">\n'
            '<link href="/path/to/css2" media="all" rel="stylesheet">',
        )

        self.assertEqual(
            str(w1.media["js"]),
            """<script src="/path/to/js1"></script>
<script src="http://media.other.com/path/to/js2"></script>
<script src="https://secure.other.com/path/to/js3"></script>""",
        )