def test_disabled_has_changed(self):
        f = MultipleChoiceField(choices=[("1", "One"), ("2", "Two")], disabled=True)
        self.assertIs(f.has_changed("x", "y"), False)