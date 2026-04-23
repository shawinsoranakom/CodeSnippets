def test_property_names_conflict_with_member_names(self):
        with self.assertRaises(AttributeError):
            models.TextChoices("Properties", "choices labels names values")