def test_render_check_exception(self):
        """
        Calling check_test() shouldn't swallow exceptions (#17888).
        """
        widget = CheckboxInput(
            check_test=lambda value: value.startswith("hello"),
        )

        with self.assertRaises(AttributeError):
            widget.render("greeting", True)