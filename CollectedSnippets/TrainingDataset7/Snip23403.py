def test_render(self):
        self.check_html(
            self.widget,
            "msg",
            "value",
            html=('<textarea rows="10" cols="40" name="msg">value</textarea>'),
        )