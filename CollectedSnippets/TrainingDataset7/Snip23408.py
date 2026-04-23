def test_mark_safe(self):
        self.check_html(
            self.widget,
            "msg",
            mark_safe("pre &quot;quoted&quot; value"),
            html=(
                '<textarea rows="10" cols="40" name="msg">pre &quot;quoted&quot; value'
                "</textarea>"
            ),
        )