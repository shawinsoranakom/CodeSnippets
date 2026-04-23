def test_has_changed(self):
        field = SimpleArrayField(forms.IntegerField())
        self.assertIs(field.has_changed([1, 2], [1, 2]), False)
        self.assertIs(field.has_changed([1, 2], "1,2"), False)
        self.assertIs(field.has_changed([1, 2], "1,2,3"), True)
        self.assertIs(field.has_changed([1, 2], "a,b"), True)