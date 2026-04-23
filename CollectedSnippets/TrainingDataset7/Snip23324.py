def test_render_selected(self):
        """
        Only one option can be selected.
        """
        choices = [("0", "0"), ("1", "1"), ("2", "2"), ("3", "3"), ("0", "extra")]
        html = """
        <div>
          <div>
            <label><input checked type="radio" name="choices" value="0">0</label>
          </div>
          <div>
            <label><input type="radio" name="choices" value="1">1</label>
          </div>
          <div>
            <label><input type="radio" name="choices" value="2">2</label>
          </div>
          <div>
            <label><input type="radio" name="choices" value="3">3</label>
          </div>
          <div>
            <label><input type="radio" name="choices" value="0">extra</label>
          </div>
        </div>
        """
        self.check_html(self.widget(choices=choices), "choices", "0", html=html)