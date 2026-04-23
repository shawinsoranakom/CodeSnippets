def test_render_label_value(self):
        """
        If the value corresponds to a label (but not to an option value), none
        of the options are selected.
        """
        html = """
        <div>
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
        self.check_html(self.widget(choices=self.beatles), "beatle", "Ringo", html=html)