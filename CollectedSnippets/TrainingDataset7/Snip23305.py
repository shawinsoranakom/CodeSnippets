def test_render_none(self):
        self.check_html(
            self.widget,
            "is_cool",
            None,
            html=("""<select name="is_cool">
            <option value="unknown" selected>Unknown</option>
            <option value="true">Yes</option>
            <option value="false">No</option>
            </select>"""),
        )