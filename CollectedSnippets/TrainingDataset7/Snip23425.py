def test_format(self):
        """
        Use 'format' to change the way a value is displayed.
        """
        t = time(12, 51, 34, 482548)
        widget = TimeInput(format="%H:%M", attrs={"type": "time"})
        self.check_html(
            widget, "time", t, html='<input type="time" name="time" value="12:51">'
        )