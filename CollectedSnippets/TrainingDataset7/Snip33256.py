def test_wrap(self):
        self.assertEqual(
            wordwrap(
                "this is a long paragraph of text that really needs to be wrapped I'm "
                "afraid",
                14,
            ),
            "this is a long\nparagraph of\ntext that\nreally needs\nto be wrapped\n"
            "I'm afraid",
        )