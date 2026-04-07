def test_get_context_does_not_mutate_attrs(self):
        attrs = {"checked": False}
        self.widget.get_context("name", True, attrs)
        self.assertIs(attrs["checked"], False)