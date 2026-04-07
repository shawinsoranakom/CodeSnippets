def test_render_attrs(self):
        """
        Attributes provided at render-time are passed to the constituent
        inputs.
        """
        html = """
        <div id="bar">
          <div>
            <label for="bar_0">
            <input checked type="radio" id="bar_0" value="J" name="beatle">John</label>
          </div>
          <div><label for="bar_1">
            <input type="radio" id="bar_1" value="P" name="beatle">Paul</label>
          </div>
          <div><label for="bar_2">
            <input type="radio" id="bar_2" value="G" name="beatle">George</label>
          </div>
          <div><label for="bar_3">
            <input type="radio" id="bar_3" value="R" name="beatle">Ringo</label>
          </div>
        </div>
        """
        self.check_html(
            self.widget(choices=self.beatles),
            "beatle",
            "J",
            attrs={"id": "bar"},
            html=html,
        )