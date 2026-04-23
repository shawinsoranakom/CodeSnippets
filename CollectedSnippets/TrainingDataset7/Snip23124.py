def test_media_inheritance_single_type(self):
        # A widget can enable inheritance of one media type by specifying
        # extend as a tuple.
        class MyWidget1(TextInput):
            class Media:
                css = {"all": ("path/to/css1", "/path/to/css2")}
                js = (
                    "/path/to/js1",
                    "http://media.other.com/path/to/js2",
                    "https://secure.other.com/path/to/js3",
                )

        class MyWidget12(MyWidget1):
            class Media:
                extend = ("css",)
                css = {"all": ("/path/to/css3", "path/to/css1")}
                js = ("/path/to/js1", "/path/to/js4")

        w12 = MyWidget12()
        self.assertEqual(
            str(w12.media),
            """<link href="/path/to/css3" media="all" rel="stylesheet">
<link href="http://media.example.com/static/path/to/css1" media="all" rel="stylesheet">
<link href="/path/to/css2" media="all" rel="stylesheet">
<script src="/path/to/js1"></script>
<script src="/path/to/js4"></script>""",
        )