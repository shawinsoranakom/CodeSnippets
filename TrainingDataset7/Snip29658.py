def test_delimiter_with_nesting(self):
        field = SimpleArrayField(SimpleArrayField(forms.CharField()), delimiter="|")
        value = field.clean("a,b|c,d")
        self.assertEqual(value, [["a", "b"], ["c", "d"]])