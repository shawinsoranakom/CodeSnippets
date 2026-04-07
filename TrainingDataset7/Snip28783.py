def test_get_data_field(self):
        field_info = self._details(Person, Person._meta.get_field("data_abstract"))
        self.assertEqual(field_info[1:], (BasePerson, True, False))
        self.assertIsInstance(field_info[0], CharField)