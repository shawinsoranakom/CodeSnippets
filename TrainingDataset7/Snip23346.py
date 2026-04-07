def test_compare_to_str(self):
        """
        The value is compared to its str().
        """
        self.check_html(
            self.widget(choices=[("1", "1"), ("2", "2"), ("3", "3")]),
            "num",
            2,
            html=("""<select name="num">
                <option value="1">1</option>
                <option value="2" selected>2</option>
                <option value="3">3</option>
                </select>"""),
        )
        self.check_html(
            self.widget(choices=[(1, 1), (2, 2), (3, 3)]),
            "num",
            "2",
            html=("""<select name="num">
                <option value="1">1</option>
                <option value="2" selected>2</option>
                <option value="3">3</option>
                </select>"""),
        )
        self.check_html(
            self.widget(choices=[(1, 1), (2, 2), (3, 3)]),
            "num",
            2,
            html=("""<select name="num">
                <option value="1">1</option>
                <option value="2" selected>2</option>
                <option value="3">3</option>
                </select>"""),
        )