def test_format(self):
        """
        Use 'format' to change the way a value is displayed.
        """
        d = date(2007, 9, 17)
        widget = DateInput(format="%d/%m/%Y", attrs={"type": "date"})
        self.check_html(
            widget, "date", d, html='<input type="date" name="date" value="17/09/2007">'
        )