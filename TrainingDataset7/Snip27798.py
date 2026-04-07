def test_nullbooleanfield_blank(self):
        """
        NullBooleanField shouldn't throw a validation error when given a value
        of None.
        """
        nullboolean = NullBooleanModel(nbfield=None)
        nullboolean.full_clean()