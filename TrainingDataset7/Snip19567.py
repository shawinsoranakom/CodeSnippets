def test_composite_pk_cannot_have_a_default(self):
        expected_message = "CompositePrimaryKey cannot have a default."
        with self.assertRaisesMessage(ValueError, expected_message):
            models.CompositePrimaryKey("tenant_id", "id", default=(1, 1))