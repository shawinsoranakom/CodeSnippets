def test_render_as_subwidget(self):
        """A RadioSelect as a subwidget of MultiWidget."""
        choices = BLANK_CHOICE_DASH + self.beatles
        html = """
        <div>
          <div><label>
            <input type="radio" name="beatle_0" value="">------</label>
          </div>
          <div><label>
            <input checked type="radio" name="beatle_0" value="J">John</label>
          </div>
          <div><label>
            <input type="radio" name="beatle_0" value="P">Paul</label>
          </div>
          <div><label>
            <input type="radio" name="beatle_0" value="G">George</label>
          </div>
          <div><label>
            <input type="radio" name="beatle_0" value="R">Ringo</label>
          </div>
        </div>
        <input name="beatle_1" type="text" value="Some text">
        """
        self.check_html(
            MultiWidget([self.widget(choices=choices), TextInput()]),
            "beatle",
            ["J", "Some text"],
            html=html,
        )