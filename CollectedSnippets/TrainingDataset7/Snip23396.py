def test_render_empty(self):
        self.check_html(
            self.widget,
            "date",
            "",
            html=(
                '<input type="hidden" name="date_0"><input type="hidden" name="date_1">'
            ),
        )