def test_render_value_1(self):
        self.check_html(
            self.widget,
            "is_cool",
            "1",
            html=("""<select name="is_cool">
            <option value="unknown" selected>Unknown</option>
            <option value="true">Yes</option>
            <option value="false">No</option>
            </select>"""),
        )