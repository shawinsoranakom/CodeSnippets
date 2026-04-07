def test_nullbooleanfield_get_prep_value(self):
        self._test_get_prep_value(models.BooleanField(null=True))