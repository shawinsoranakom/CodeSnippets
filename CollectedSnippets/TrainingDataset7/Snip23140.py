def test_media_deduplication(self):
        # The deduplication doesn't only happen at the point of merging two or
        # more media objects.
        media = Media(
            css={
                "all": (
                    CSS("/path/to/css1", media="all"),
                    CSS("/path/to/css1", media="all"),
                    "/path/to/css1",
                )
            },
            js=(Script("/path/to/js1"), Script("/path/to/js1"), "/path/to/js1"),
        )
        self.assertHTMLEqual(
            str(media),
            '<link href="/path/to/css1" media="all" rel="stylesheet">\n'
            '<script src="/path/to/js1"></script>',
        )