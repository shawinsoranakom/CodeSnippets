def test_media_property_parent_references(self):
        # Media properties can reference the media of their parents,
        # even if the parent media was defined using a class
        class MyWidget1(TextInput):
            class Media:
                css = {"all": ("path/to/css1", "/path/to/css2")}
                js = (
                    "/path/to/js1",
                    "http://media.other.com/path/to/js2",
                    "https://secure.other.com/path/to/js3",
                )

        class MyWidget6(MyWidget1):
            def _media(self):
                return super().media + Media(
                    css={"all": ("/other/path",)}, js=("/other/js",)
                )

            media = property(_media)

        w6 = MyWidget6()
        self.assertEqual(
            str(w6.media),
            '<link href="http://media.example.com/static/path/to/css1" media="all" '
            'rel="stylesheet">\n'
            '<link href="/other/path" media="all" rel="stylesheet">\n'
            '<link href="/path/to/css2" media="all" rel="stylesheet">\n'
            '<script src="/path/to/js1"></script>\n'
            '<script src="/other/js"></script>\n'
            '<script src="http://media.other.com/path/to/js2"></script>\n'
            '<script src="https://secure.other.com/path/to/js3"></script>',
        )