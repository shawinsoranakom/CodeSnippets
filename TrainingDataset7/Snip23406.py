def test_render_none(self):
        self.check_html(
            self.widget,
            "msg",
            None,
            html='<textarea rows="10" cols="40" name="msg"></textarea>',
        )