def test_render_value_label(self):
        """
        If the value corresponds to a label (but not to an option value), none
        of the options are selected.
        """
        self.check_html(
            self.widget(choices=self.beatles),
            "beatles",
            ["John"],
            html=("""<select multiple name="beatles">
            <option value="J">John</option>
            <option value="P">Paul</option>
            <option value="G">George</option>
            <option value="R">Ringo</option>
            </select>"""),
        )