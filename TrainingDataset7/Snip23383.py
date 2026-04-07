def test_multiple_values_invalid(self):
        """
        If multiple values are given, but some of them are not valid, the valid
        ones are selected.
        """
        self.check_html(
            self.widget(choices=self.beatles),
            "beatles",
            ["J", "G", "foo"],
            html=("""<select multiple name="beatles">
            <option value="J" selected>John</option>
            <option value="P">Paul</option>
            <option value="G" selected>George</option>
            <option value="R">Ringo</option>
            </select>"""),
        )