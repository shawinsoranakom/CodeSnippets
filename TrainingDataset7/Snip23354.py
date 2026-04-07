def test_doesnt_localize_option_value(self):
        choices = [
            (1, "One"),
            (1000, "One thousand"),
            (1000000, "One million"),
        ]
        html = """
        <select name="number">
        <option value="1">One</option>
        <option value="1000">One thousand</option>
        <option value="1000000">One million</option>
        </select>
        """
        self.check_html(self.widget(choices=choices), "number", None, html=html)

        choices = [
            (datetime.time(0, 0), "midnight"),
            (datetime.time(12, 0), "noon"),
        ]
        html = """
        <select name="time">
        <option value="00:00:00">midnight</option>
        <option value="12:00:00">noon</option>
        </select>
        """
        self.check_html(self.widget(choices=choices), "time", None, html=html)