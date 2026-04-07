def test_composite_pk_must_include_at_least_2_fields(self):
        expected_message = "CompositePrimaryKey must include at least two fields."
        with self.assertRaisesMessage(ValueError, expected_message):
            models.CompositePrimaryKey("id")