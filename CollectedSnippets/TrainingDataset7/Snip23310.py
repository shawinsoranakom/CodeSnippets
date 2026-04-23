def test_render_value_2(self):
        self.check_html(
            self.widget,
            "is_cool",
            "2",
            html=("""<select name="is_cool">
            <option value="unknown">Unknown</option>
            <option value="true" selected>Yes</option>
            <option value="false">No</option>
            </select>"""),
        )