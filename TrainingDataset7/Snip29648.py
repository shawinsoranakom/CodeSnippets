def test_with_size_singular(self):
        field = ArrayField(models.IntegerField(), size=1)
        field.clean([1], None)
        msg = "List contains 2 items, it should contain no more than 1."
        with self.assertRaisesMessage(exceptions.ValidationError, msg):
            field.clean([1, 2], None)