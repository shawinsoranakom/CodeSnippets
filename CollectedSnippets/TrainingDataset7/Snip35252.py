def test_ignore_comments(self):
        self.assertHTMLEqual(
            "<div>Hello<!-- this is a comment --> World!</div>",
            "<div>Hello World!</div>",
        )