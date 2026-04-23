def test_min_length(self):
        field = SimpleArrayField(forms.CharField(), min_length=4)
        msg = "List contains 3 items, it should contain no fewer than 4."
        with self.assertRaisesMessage(exceptions.ValidationError, msg):
            field.clean("a,b,c")