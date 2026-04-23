def test_get_related_m2m(self):
        field_info = self._details(Person, Person._meta.get_field("relating_people"))
        self.assertEqual(field_info[1:], (None, False, True))
        self.assertIsInstance(field_info[0], ForeignObjectRel)