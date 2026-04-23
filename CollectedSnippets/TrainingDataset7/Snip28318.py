def test_empty_fields_to_fields_for_model(self):
        """
        An argument of fields=() to fields_for_model should return an empty
        dictionary
        """
        field_dict = fields_for_model(Person, fields=())
        self.assertEqual(len(field_dict), 0)