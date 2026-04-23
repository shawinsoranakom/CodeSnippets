def test_render_true(self):
        self.check_html(
            self.widget,
            "is_cool",
            True,
            html=("""<select name="is_cool">
            <option value="unknown">Unknown</option>
            <option value="true" selected>Yes</option>
            <option value="false">No</option>
            </select>"""),
        )