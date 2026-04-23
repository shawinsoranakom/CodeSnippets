def test_has_changed_same(self):
        self.assertFalse(
            self.field.has_changed(
                "some text,JP,2007-04-25 06:24:00",
                ["some text", ["J", "P"], ["2007-04-25", "6:24:00"]],
            )
        )