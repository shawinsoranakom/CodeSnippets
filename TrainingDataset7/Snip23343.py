def test_render_label_value(self):
        """
        If the value corresponds to a label (but not to an option value), none
        of the options are selected.
        """
        self.check_html(
            self.widget(choices=self.beatles),
            "beatle",
            "John",
            html=("""<select name="beatle">
            <option value="J">John</option>
            <option value="P">Paul</option>
            <option value="G">George</option>
            <option value="R">Ringo</option>
            </select>"""),
        )