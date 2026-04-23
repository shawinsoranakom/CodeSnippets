def test_media_inheritance_from_property(self):
        # If a widget extends another but defines media, it extends the parents
        # widget's media, even if the parent defined media using a property.
        class MyWidget1(TextInput):
            class Media:
                css = {"all": ("path/to/css1", "/path/to/css2")}
                js = (
                    "/path/to/js1",
                    "http://media.other.com/path/to/js2",
                    "https://secure.other.com/path/to/js3",
                )

        class MyWidget4(TextInput):
            def _media(self):
                return Media(css={"all": ("/some/path",)}, js=("/some/js",))

            media = property(_media)

        class MyWidget9(MyWidget4):
            class Media:
                css = {"all": ("/other/path",)}
                js = ("/other/js",)

        w9 = MyWidget9()
        self.assertEqual(
            str(w9.media),
            """<link href="/some/path" media="all" rel="stylesheet">
<link href="/other/path" media="all" rel="stylesheet">
<script src="/some/js"></script>
<script src="/other/js"></script>""",
        )

        # A widget can disable media inheritance by specifying 'extend=False'
        class MyWidget10(MyWidget1):
            class Media:
                extend = False
                css = {"all": ("/path/to/css3", "path/to/css1")}
                js = ("/path/to/js1", "/path/to/js4")

        w10 = MyWidget10()
        self.assertEqual(
            str(w10.media),
            """<link href="/path/to/css3" media="all" rel="stylesheet">
<link href="http://media.example.com/static/path/to/css1" media="all" rel="stylesheet">
<script src="/path/to/js1"></script>
<script src="/path/to/js4"></script>""",
        )