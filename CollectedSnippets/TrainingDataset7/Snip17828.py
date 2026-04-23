def test_bug_19349_render_with_none_value(self):
        # Rendering the widget with value set to None
        # mustn't raise an exception.
        widget = ReadOnlyPasswordHashWidget()
        html = widget.render(name="password", value=None, attrs={})
        self.assertIn(_("No password set."), html)