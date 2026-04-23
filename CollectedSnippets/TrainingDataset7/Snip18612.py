def test_boolean_constraints(self):
        """Boolean fields have check constraints on their values."""
        for field in (BooleanField(), BooleanField(null=True)):
            with self.subTest(field=field):
                field.set_attributes_from_name("is_nice")
                self.assertIn('"IS_NICE" IN (0,1)', field.db_check(connection))