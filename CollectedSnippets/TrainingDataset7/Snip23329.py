def test_choices_escaping(self):
        choices = (("bad", "you & me"), ("good", mark_safe("you &gt; me")))
        html = """
        <div>
          <div>
            <label><input type="radio" name="escape" value="bad">you & me</label>
          </div>
          <div>
            <label><input type="radio" name="escape" value="good">you &gt; me</label>
          </div>
        </div>
        """
        self.check_html(self.widget(choices=choices), "escape", None, html=html)