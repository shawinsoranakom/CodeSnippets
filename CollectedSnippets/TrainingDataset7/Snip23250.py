def test_render(self):
        self.check_html(
            self.widget,
            "color",
            "",
            html="<input type='color' name='color'>",
        )