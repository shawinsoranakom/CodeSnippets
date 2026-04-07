def test_optgroup_select_multiple(self):
        widget = SelectMultiple(
            choices=(
                ("outer1", "Outer 1"),
                ('Group "1"', (("inner1", "Inner 1"), ("inner2", "Inner 2"))),
            )
        )
        self.check_html(
            widget,
            "nestchoice",
            ["outer1", "inner2"],
            html=("""<select multiple name="nestchoice">
            <option value="outer1" selected>Outer 1</option>
            <optgroup label="Group &quot;1&quot;">
            <option value="inner1">Inner 1</option>
            <option value="inner2" selected>Inner 2</option>
            </optgroup>
            </select>"""),
        )