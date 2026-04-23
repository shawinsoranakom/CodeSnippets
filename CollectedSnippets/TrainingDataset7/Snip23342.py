def test_render_none(self):
        """
        If the value is None, none of the options are selected.
        """
        self.check_html(
            self.widget(choices=self.beatles),
            "beatle",
            None,
            html=("""<select name="beatle">
            <option value="J">John</option>
            <option value="P">Paul</option>
            <option value="G">George</option>
            <option value="R">Ringo</option>
            </select>"""),
        )