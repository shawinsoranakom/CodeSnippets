def test_str(self):
        self.assertHTMLEqual(
            str(Script("path/to/js")),
            '<script src="http://media.example.com/static/path/to/js"></script>',
        )
        self.assertHTMLEqual(
            str(Script("path/to/js", **{"async": True, "deferred": False})),
            '<script src="http://media.example.com/static/path/to/js" async></script>',
        )