def test_choices_constructor(self):
        widget = self.widget(choices=[(1, 1), (2, 2), (3, 3)])
        html = """
        <div>
          <div>
            <label><input type="radio" name="num" value="1">1</label>
          </div>
          <div>
            <label><input type="radio" name="num" value="2">2</label>
          </div>
          <div>
            <label><input checked type="radio" name="num" value="3">3</label>
          </div>
        </div>
        """
        self.check_html(widget, "num", 3, html=html)