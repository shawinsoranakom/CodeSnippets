def test_render_selected(self):
        """
        Only one option can be selected (#8103).
        """
        choices = [("0", "0"), ("1", "1"), ("2", "2"), ("3", "3"), ("0", "extra")]

        self.check_html(
            self.widget(choices=choices),
            "choices",
            "0",
            html=("""<select name="choices">
            <option value="0" selected>0</option>
            <option value="1">1</option>
            <option value="2">2</option>
            <option value="3">3</option>
            <option value="0">extra</option>
            </select>"""),
        )