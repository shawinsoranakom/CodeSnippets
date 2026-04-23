def test_get_generic_relation(self):
        field_info = self._details(
            Person, Person._meta.get_field("generic_relation_base")
        )
        self.assertEqual(field_info[1:], (None, True, False))
        self.assertIsInstance(field_info[0], GenericRelation)