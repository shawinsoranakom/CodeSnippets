def test_media_property(self):
        ###############################################################
        # Property-based media definitions
        ###############################################################

        # Widget media can be defined as a property
        class MyWidget4(TextInput):
            def _media(self):
                return Media(css={"all": ("/some/path",)}, js=("/some/js",))

            media = property(_media)

        w4 = MyWidget4()
        self.assertEqual(
            str(w4.media),
            """<link href="/some/path" media="all" rel="stylesheet">
<script src="/some/js"></script>""",
        )

        # Media properties can reference the media of their parents
        class MyWidget5(MyWidget4):
            def _media(self):
                return super().media + Media(
                    css={"all": ("/other/path",)}, js=("/other/js",)
                )

            media = property(_media)

        w5 = MyWidget5()
        self.assertEqual(
            str(w5.media),
            """<link href="/some/path" media="all" rel="stylesheet">
<link href="/other/path" media="all" rel="stylesheet">
<script src="/some/js"></script>
<script src="/other/js"></script>""",
        )