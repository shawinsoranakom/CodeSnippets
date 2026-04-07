def test_min_length_singular(self):
        field = SimpleArrayField(forms.IntegerField(), min_length=2)
        field.clean([1, 2])
        msg = "List contains 1 item, it should contain no fewer than 2."
        with self.assertRaisesMessage(exceptions.ValidationError, msg):
            field.clean([1])