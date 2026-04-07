def test_get_related_object(self):
        field_info = self._details(
            Person, Person._meta.get_field("relating_baseperson")
        )
        self.assertEqual(field_info[1:], (BasePerson, False, False))
        self.assertIsInstance(field_info[0], ForeignObjectRel)