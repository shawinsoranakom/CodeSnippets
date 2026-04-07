def test_sequence_name_length_limits_create(self):
        """Creation of model with long name and long pk name doesn't error."""
        VeryLongModelNameZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ.objects.create()