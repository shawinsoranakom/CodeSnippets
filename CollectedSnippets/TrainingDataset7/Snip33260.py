def test_wrap_lazy_string(self):
        self.assertEqual(
            wordwrap(
                lazystr(
                    "this is a long paragraph of text that really needs to be wrapped "
                    "I'm afraid"
                ),
                14,
            ),
            "this is a long\nparagraph of\ntext that\nreally needs\nto be wrapped\n"
            "I'm afraid",
        )