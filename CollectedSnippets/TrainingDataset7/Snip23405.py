def test_render_empty(self):
        self.check_html(
            self.widget,
            "msg",
            "",
            html='<textarea rows="10" cols="40" name="msg"></textarea>',
        )