def test_disabled_has_changed(self):
        f = BooleanField(disabled=True)
        self.assertIs(f.has_changed("True", "False"), False)