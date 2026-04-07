def test_integerfield_validates_zero_against_choices(self):
        f = models.IntegerField(choices=((1, 1),))
        with self.assertRaises(ValidationError):
            f.clean("0", None)