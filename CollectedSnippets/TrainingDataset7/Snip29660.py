def test_max_length(self):
        field = SimpleArrayField(forms.CharField(), max_length=2)
        msg = "List contains 3 items, it should contain no more than 2."
        with self.assertRaisesMessage(exceptions.ValidationError, msg):
            field.clean("a,b,c")