def test_composite_pk_must_be_blank(self):
        expected_message = "CompositePrimaryKey must be blank."
        with self.assertRaisesMessage(ValueError, expected_message):
            models.CompositePrimaryKey("tenant_id", "id", blank=False)