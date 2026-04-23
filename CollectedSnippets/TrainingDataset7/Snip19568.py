def test_composite_pk_cannot_have_a_database_default(self):
        expected_message = "CompositePrimaryKey cannot have a database default."
        with self.assertRaisesMessage(ValueError, expected_message):
            models.CompositePrimaryKey("tenant_id", "id", db_default=models.F("id"))