def test_clean(self):
        self.assertEqual(
            self.field.clean(["some text", ["J", "P"], ["2007-04-25", "6:24:00"]]),
            "some text,JP,2007-04-25 06:24:00",
        )