def test_media_deduplication(self):
        # A deduplication test applied directly to a Media object, to confirm
        # that the deduplication doesn't only happen at the point of merging
        # two or more media objects.
        media = Media(
            css={"all": ("/path/to/css1", "/path/to/css1")},
            js=("/path/to/js1", "/path/to/js1"),
        )
        self.assertEqual(
            str(media),
            """<link href="/path/to/css1" media="all" rel="stylesheet">
<script src="/path/to/js1"></script>""",
        )