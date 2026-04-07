def test_render_none(self):
        self.check_html(
            self.widget,
            "date",
            None,
            html=('<input type="text" name="date_0"><input type="text" name="date_1">'),
        )