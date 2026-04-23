def test_render_selected(self):
        self.check_html(
            self.widget(choices=self.beatles),
            "beatles",
            ["J"],
            html=("""<select multiple name="beatles">
            <option value="J" selected>John</option>
            <option value="P">Paul</option>
            <option value="G">George</option>
            <option value="R">Ringo</option>
            </select>"""),
        )