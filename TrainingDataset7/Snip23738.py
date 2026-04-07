def test_unknown_week_format(self):
        msg = "Unknown week format '%T'. Choices are: %U, %V, %W"
        with self.assertRaisesMessage(ValueError, msg):
            self.client.get("/dates/books/2008/week/39/unknown_week_format/")