def test_composite_pk_cannot_have_a_db_column(self):
        expected_message = "CompositePrimaryKey cannot have a db_column."
        with self.assertRaisesMessage(ValueError, expected_message):
            models.CompositePrimaryKey("tenant_id", "id", db_column="tenant_pk")