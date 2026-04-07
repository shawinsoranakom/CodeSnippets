def test_clear_input_renders_only_if_initial(self):
        """
        A ClearableFileInput instantiated with no initial value does not render
        a clear checkbox.
        """
        self.check_html(
            self.widget, "myfile", None, html='<input type="file" name="myfile">'
        )