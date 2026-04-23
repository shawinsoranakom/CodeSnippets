def test_media_inheritance_extends(self):
        # A widget can explicitly enable full media inheritance by specifying
        # 'extend=True'.
        class MyWidget1(TextInput):
            class Media:
                css = {"all": ("path/to/css1", "/path/to/css2")}
                js = (
                    "/path/to/js1",
                    "http://media.other.com/path/to/js2",
                    "https://secure.other.com/path/to/js3",
                )

        class MyWidget11(MyWidget1):
            class Media:
                extend = True
                css = {"all": ("/path/to/css3", "path/to/css1")}
                js = ("/path/to/js1", "/path/to/js4")

        w11 = MyWidget11()
        self.assertEqual(
            str(w11.media),
            """<link href="/path/to/css3" media="all" rel="stylesheet">
<link href="http://media.example.com/static/path/to/css1" media="all" rel="stylesheet">
<link href="/path/to/css2" media="all" rel="stylesheet">
<script src="/path/to/js1"></script>
<script src="http://media.other.com/path/to/js2"></script>
<script src="/path/to/js4"></script>
<script src="https://secure.other.com/path/to/js3"></script>""",
        )