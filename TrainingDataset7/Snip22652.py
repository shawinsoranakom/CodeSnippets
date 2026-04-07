def test_has_changed_last_widget(self):
        """
        Test when the last widget's data has changed. This ensures that it is
        not short circuiting while testing the widgets.
        """
        self.assertTrue(
            self.field.has_changed(
                "some text,JP,2007-04-25 06:24:00",
                ["some text", ["J", "P"], ["2009-04-25", "11:44:00"]],
            )
        )