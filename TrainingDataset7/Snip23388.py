def test_render_empty(self):
        self.check_html(
            self.widget,
            "date",
            "",
            html=('<input type="text" name="date_0"><input type="text" name="date_1">'),
        )