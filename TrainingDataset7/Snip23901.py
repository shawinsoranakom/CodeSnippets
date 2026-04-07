def test_get_or_create_invalid_params(self):
        """
        If you don't specify a value or default value for all required
        fields, you will get an error.
        """
        with self.assertRaises(IntegrityError):
            Person.objects.get_or_create(first_name="Tom", last_name="Smith")