def test_render_as_subwidget(self):
        """A RadioSelect as a subwidget of MultiWidget."""
        choices = (("", "------"),) + self.beatles
        self.check_html(
            MultiWidget([self.widget(choices=choices), TextInput()]),
            "beatle",
            ["J", "Some text"],
            html=("""
                <select name="beatle_0">
                  <option value="">------</option>
                  <option value="J" selected>John</option>
                  <option value="P">Paul</option>
                  <option value="G">George</option>
                  <option value="R">Ringo</option>
                </select>
                <input name="beatle_1" type="text" value="Some text">
                """),
        )