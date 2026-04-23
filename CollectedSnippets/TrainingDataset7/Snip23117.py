def test_combine_media(self):
        # Media objects can be combined. Any given media resource will appear
        # only once. Duplicated media definitions are ignored.
        class MyWidget1(TextInput):
            class Media:
                css = {"all": ("path/to/css1", "/path/to/css2")}
                js = (
                    "/path/to/js1",
                    "http://media.other.com/path/to/js2",
                    "https://secure.other.com/path/to/js3",
                )

        class MyWidget2(TextInput):
            class Media:
                css = {"all": ("/path/to/css2", "/path/to/css3")}
                js = ("/path/to/js1", "/path/to/js4")

        class MyWidget3(TextInput):
            class Media:
                css = {"all": ("path/to/css1", "/path/to/css3")}
                js = ("/path/to/js1", "/path/to/js4")

        w1 = MyWidget1()
        w2 = MyWidget2()
        w3 = MyWidget3()
        self.assertEqual(
            str(w1.media + w2.media + w3.media),
            '<link href="http://media.example.com/static/path/to/css1" media="all" '
            'rel="stylesheet">\n'
            '<link href="/path/to/css2" media="all" rel="stylesheet">\n'
            '<link href="/path/to/css3" media="all" rel="stylesheet">\n'
            '<script src="/path/to/js1"></script>\n'
            '<script src="http://media.other.com/path/to/js2"></script>\n'
            '<script src="/path/to/js4"></script>\n'
            '<script src="https://secure.other.com/path/to/js3"></script>',
        )

        # media addition hasn't affected the original objects
        self.assertEqual(
            str(w1.media),
            '<link href="http://media.example.com/static/path/to/css1" media="all" '
            'rel="stylesheet">\n'
            '<link href="/path/to/css2" media="all" rel="stylesheet">\n'
            '<script src="/path/to/js1"></script>\n'
            '<script src="http://media.other.com/path/to/js2"></script>\n'
            '<script src="https://secure.other.com/path/to/js3"></script>',
        )

        # Regression check for #12879: specifying the same CSS or JS file
        # multiple times in a single Media instance should result in that file
        # only being included once.
        class MyWidget4(TextInput):
            class Media:
                css = {"all": ("/path/to/css1", "/path/to/css1")}
                js = ("/path/to/js1", "/path/to/js1")

        w4 = MyWidget4()
        self.assertEqual(
            str(w4.media),
            """<link href="/path/to/css1" media="all" rel="stylesheet">
<script src="/path/to/js1"></script>""",
        )