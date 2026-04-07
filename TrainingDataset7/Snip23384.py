def test_compare_string(self):
        choices = [("1", "1"), ("2", "2"), ("3", "3")]

        self.check_html(
            self.widget(choices=choices),
            "nums",
            [2],
            html=("""<select multiple name="nums">
            <option value="1">1</option>
            <option value="2" selected>2</option>
            <option value="3">3</option>
            </select>"""),
        )

        self.check_html(
            self.widget(choices=choices),
            "nums",
            ["2"],
            html=("""<select multiple name="nums">
            <option value="1">1</option>
            <option value="2" selected>2</option>
            <option value="3">3</option>
            </select>"""),
        )

        self.check_html(
            self.widget(choices=choices),
            "nums",
            [2],
            html=("""<select multiple name="nums">
            <option value="1">1</option>
            <option value="2" selected>2</option>
            <option value="3">3</option>
            </select>"""),
        )