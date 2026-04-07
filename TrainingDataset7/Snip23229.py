def test_clear_input_renders_only_if_not_required(self):
        """
        A ClearableFileInput with is_required=True does not render a clear
        checkbox.
        """
        widget = ClearableFileInput()
        widget.is_required = True
        self.check_html(
            widget,
            "myfile",
            FakeFieldFile(),
            html=("""
            Currently: <a href="something">something</a> <br>
            Change: <input type="file" name="myfile">
            """),
        )