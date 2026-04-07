def test_render_required(self):
        widget = Textarea()
        widget.is_required = True
        self.check_html(
            widget,
            "msg",
            "value",
            html='<textarea rows="10" cols="40" name="msg">value</textarea>',
        )