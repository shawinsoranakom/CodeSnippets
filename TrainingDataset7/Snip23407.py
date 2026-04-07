def test_escaping(self):
        self.check_html(
            self.widget,
            "msg",
            'some "quoted" & ampersanded value',
            html=(
                '<textarea rows="10" cols="40" name="msg">'
                "some &quot;quoted&quot; &amp; ampersanded value</textarea>"
            ),
        )