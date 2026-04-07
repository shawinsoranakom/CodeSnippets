def test_doesnt_localize_input_value(self):
        choices = [
            (1, "One"),
            (1000, "One thousand"),
            (1000000, "One million"),
        ]
        html = """
        <div>
          <div><label><input type="radio" name="number" value="1">One</label></div>
          <div>
            <label><input type="radio" name="number" value="1000">One thousand</label>
          </div>
          <div>
            <label><input type="radio" name="number" value="1000000">One million</label>
          </div>
        </div>
        """
        self.check_html(self.widget(choices=choices), "number", None, html=html)

        choices = [
            (datetime.time(0, 0), "midnight"),
            (datetime.time(12, 0), "noon"),
        ]
        html = """
        <div>
          <div>
            <label><input type="radio" name="time" value="00:00:00">midnight</label>
          </div>
          <div>
            <label><input type="radio" name="time" value="12:00:00">noon</label>
          </div>
        </div>
        """
        self.check_html(self.widget(choices=choices), "time", None, html=html)