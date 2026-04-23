def test_choices_constructor(self):
        widget = Select(choices=[(1, 1), (2, 2), (3, 3)])
        self.check_html(
            widget,
            "num",
            2,
            html=("""<select name="num">
            <option value="1">1</option>
            <option value="2" selected>2</option>
            <option value="3">3</option>
            </select>"""),
        )