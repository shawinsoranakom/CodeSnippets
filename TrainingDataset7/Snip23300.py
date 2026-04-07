def test_no_whitespace_between_widgets(self):
        widget = MyMultiWidget(widgets=(TextInput, TextInput()))
        self.check_html(
            widget,
            "code",
            None,
            html=('<input type="text" name="code_0"><input type="text" name="code_1">'),
            strict=True,
        )