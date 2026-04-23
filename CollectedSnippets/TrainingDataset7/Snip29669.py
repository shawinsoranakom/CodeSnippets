def test_has_changed_empty(self):
        field = SimpleArrayField(forms.CharField())
        self.assertIs(field.has_changed(None, None), False)
        self.assertIs(field.has_changed(None, ""), False)
        self.assertIs(field.has_changed(None, []), False)
        self.assertIs(field.has_changed([], None), False)
        self.assertIs(field.has_changed([], ""), False)