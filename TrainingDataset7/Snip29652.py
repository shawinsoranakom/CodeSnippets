def test_valid(self):
        field = SimpleArrayField(forms.CharField())
        value = field.clean("a,b,c")
        self.assertEqual(value, ["a", "b", "c"])