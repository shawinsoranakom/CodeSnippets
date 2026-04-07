def test_multiple_options_same_value(self):
        """
        Multiple options with the same value can be selected (#8103).
        """
        self.check_html(
            self.widget(choices=self.numeric_choices),
            "choices",
            ["0"],
            html=("""<select multiple name="choices">
            <option value="0" selected>0</option>
            <option value="1">1</option>
            <option value="2">2</option>
            <option value="3">3</option>
            <option value="0" selected>extra</option>
            </select>"""),
        )