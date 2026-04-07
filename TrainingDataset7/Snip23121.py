def test_media_inheritance(self):
        ###############################################################
        # Inheritance of media
        ###############################################################

        # If a widget extends another but provides no media definition, it
        # inherits the parent widget's media.
        class MyWidget1(TextInput):
            class Media:
                css = {"all": ("path/to/css1", "/path/to/css2")}
                js = (
                    "/path/to/js1",
                    "http://media.other.com/path/to/js2",
                    "https://secure.other.com/path/to/js3",
                )

        class MyWidget7(MyWidget1):
            pass

        w7 = MyWidget7()
        self.assertEqual(
            str(w7.media),
            '<link href="http://media.example.com/static/path/to/css1" media="all" '
            'rel="stylesheet">\n'
            '<link href="/path/to/css2" media="all" rel="stylesheet">\n'
            '<script src="/path/to/js1"></script>\n'
            '<script src="http://media.other.com/path/to/js2"></script>\n'
            '<script src="https://secure.other.com/path/to/js3"></script>',
        )

        # If a widget extends another but defines media, it extends the parent
        # widget's media by default.
        class MyWidget8(MyWidget1):
            class Media:
                css = {"all": ("/path/to/css3", "path/to/css1")}
                js = ("/path/to/js1", "/path/to/js4")

        w8 = MyWidget8()
        self.assertEqual(
            str(w8.media),
            """<link href="/path/to/css3" media="all" rel="stylesheet">
<link href="http://media.example.com/static/path/to/css1" media="all" rel="stylesheet">
<link href="/path/to/css2" media="all" rel="stylesheet">
<script src="/path/to/js1"></script>
<script src="http://media.other.com/path/to/js2"></script>
<script src="/path/to/js4"></script>
<script src="https://secure.other.com/path/to/js3"></script>""",
        )