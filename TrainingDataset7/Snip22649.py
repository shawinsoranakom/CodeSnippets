def test_has_changed_no_initial(self):
        self.assertTrue(
            self.field.has_changed(
                None, ["some text", ["J", "P"], ["2007-04-25", "6:24:00"]]
            )
        )