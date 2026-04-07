def test_multi_media(self):
        ###############################################################
        # Multi-media handling for CSS
        ###############################################################

        # A widget can define CSS media for multiple output media types
        class MultimediaWidget(TextInput):
            class Media:
                css = {
                    "screen, print": ("/file1", "/file2"),
                    "screen": ("/file3",),
                    "print": ("/file4",),
                }
                js = ("/path/to/js1", "/path/to/js4")

        multimedia = MultimediaWidget()
        self.assertEqual(
            str(multimedia.media),
            """<link href="/file4" media="print" rel="stylesheet">
<link href="/file3" media="screen" rel="stylesheet">
<link href="/file1" media="screen, print" rel="stylesheet">
<link href="/file2" media="screen, print" rel="stylesheet">
<script src="/path/to/js1"></script>
<script src="/path/to/js4"></script>""",
        )