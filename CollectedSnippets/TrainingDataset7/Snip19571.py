def test_composite_pk_must_be_a_primary_key(self):
        expected_message = "CompositePrimaryKey must be a primary key."
        with self.assertRaisesMessage(ValueError, expected_message):
            models.CompositePrimaryKey("tenant_id", "id", primary_key=False)