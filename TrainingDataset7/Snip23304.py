def test_render_false(self):
        self.check_html(
            self.widget,
            "is_cool",
            False,
            html=("""<select name="is_cool">
            <option value="unknown">Unknown</option>
            <option value="true">Yes</option>
            <option value="false" selected>No</option>
            </select>"""),
        )