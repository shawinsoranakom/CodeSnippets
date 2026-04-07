def test_combine_media(self):
        class MyWidget1(TextInput):
            class Media:
                css = {"all": (CSS("path/to/css1", media="all"), "/path/to/css2")}
                js = (
                    "/path/to/js1",
                    "http://media.other.com/path/to/js2",
                    "https://secure.other.com/path/to/js3",
                    Script(
                        "/path/to/js4", integrity="9d947b87fdeb25030d56d01f7aa75800"
                    ),
                )

        class MyWidget2(TextInput):
            class Media:
                css = {"all": (CSS("/path/to/css2", media="all"), "/path/to/css3")}
                js = (Script("/path/to/js1"), "/path/to/js4")

        w1 = MyWidget1()
        w2 = MyWidget2()
        self.assertHTMLEqual(
            str(w1.media + w2.media),
            '<link href="http://media.example.com/static/path/to/css1" media="all" '
            'rel="stylesheet">\n'
            '<link href="/path/to/css2" media="all" rel="stylesheet">\n'
            '<link href="/path/to/css3" media="all" rel="stylesheet">\n'
            '<script src="/path/to/js1"></script>\n'
            '<script src="http://media.other.com/path/to/js2"></script>\n'
            '<script src="https://secure.other.com/path/to/js3"></script>\n'
            '<script src="/path/to/js4" integrity="9d947b87fdeb25030d56d01f7aa75800">'
            "</script>",
        )