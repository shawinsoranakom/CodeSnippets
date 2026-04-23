def test_person(self):
        # Instance only descriptors don't appear in _property_names.
        self.assertEqual(BasePerson().test_instance_only_descriptor, 1)
        with self.assertRaisesMessage(AttributeError, "Instance only"):
            AbstractPerson.test_instance_only_descriptor
        self.assertEqual(
            AbstractPerson._meta._property_names, frozenset(["pk", "test_property"])
        )