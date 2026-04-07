def test_string(self):
        """
        Should be able to initialize from a string value.
        """
        self.check_html(
            self.widget,
            "date",
            "2007-09-17",
            html=('<input type="text" name="date" value="2007-09-17">'),
        )