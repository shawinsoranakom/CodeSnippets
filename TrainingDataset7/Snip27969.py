def test_integerfield_raises_error_on_invalid_intput(self):
        f = models.IntegerField()
        with self.assertRaises(ValidationError):
            f.clean("a", None)