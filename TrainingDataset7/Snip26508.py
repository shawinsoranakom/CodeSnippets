def test_repr(self):
        tests = [
            (constants.INFO, "thing", "", "Message(level=20, message='thing')"),
            (
                constants.WARNING,
                "careful",
                "tag1 tag2",
                "Message(level=30, message='careful', extra_tags='tag1 tag2')",
            ),
            (
                constants.ERROR,
                "oops",
                "tag",
                "Message(level=40, message='oops', extra_tags='tag')",
            ),
            (12, "custom", "", "Message(level=12, message='custom')"),
        ]
        for level, message, extra_tags, expected in tests:
            with self.subTest(level=level, message=message):
                msg = Message(level, message, extra_tags=extra_tags)
                self.assertEqual(repr(msg), expected)