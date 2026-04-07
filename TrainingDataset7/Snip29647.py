def test_with_size(self):
        field = ArrayField(models.IntegerField(), size=3)
        field.clean([1, 2, 3], None)
        msg = "List contains 4 items, it should contain no more than 3."
        with self.assertRaisesMessage(exceptions.ValidationError, msg):
            field.clean([1, 2, 3, 4], None)