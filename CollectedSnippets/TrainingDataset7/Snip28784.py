def test_get_m2m_field(self):
        field_info = self._details(Person, Person._meta.get_field("m2m_base"))
        self.assertEqual(field_info[1:], (BasePerson, True, True))
        self.assertIsInstance(field_info[0], ManyToManyField)