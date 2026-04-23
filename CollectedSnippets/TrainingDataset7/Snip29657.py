def test_delimiter(self):
        field = SimpleArrayField(forms.CharField(), delimiter="|")
        value = field.clean("a|b|c")
        self.assertEqual(value, ["a", "b", "c"])