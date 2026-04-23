def test_string(self):
        """Initializing from a string value."""
        self.check_html(
            self.widget,
            "time",
            "13:12:11",
            html=('<input type="text" name="time" value="13:12:11">'),
        )