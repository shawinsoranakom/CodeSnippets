def test_nullbooleanfield_to_python(self):
        self._test_to_python(models.BooleanField(null=True))