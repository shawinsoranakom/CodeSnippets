def test_disabled_has_changed(self):
        f = FileField(disabled=True)
        self.assertIs(f.has_changed("x", "y"), False)