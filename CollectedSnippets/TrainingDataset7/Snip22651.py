def test_has_changed_first_widget(self):
        """
        Test when the first widget's data has changed.
        """
        self.assertTrue(
            self.field.has_changed(
                "some text,JP,2007-04-25 06:24:00",
                ["other text", ["J", "P"], ["2007-04-25", "6:24:00"]],
            )
        )