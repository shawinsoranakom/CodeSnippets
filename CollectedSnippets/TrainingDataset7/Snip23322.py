def test_render_none(self):
        """
        If value is None, none of the options are selected.
        """
        choices = BLANK_CHOICE_DASH + self.beatles
        html = """
        <div>
          <div>
            <label><input checked type="radio" name="beatle" value="">------</label>
          </div>
          <div>
            <label><input type="radio" name="beatle" value="J">John</label>
          </div>
          <div>
            <label><input type="radio" name="beatle" value="P">Paul</label>
          </div>
          <div>
            <label><input type="radio" name="beatle" value="G">George</label>
          </div>
          <div>
            <label><input type="radio" name="beatle" value="R">Ringo</label>
          </div>
        </div>
        """
        self.check_html(self.widget(choices=choices), "beatle", None, html=html)