def test_composite_pk_cannot_be_editable(self):
        expected_message = "CompositePrimaryKey cannot be editable."
        with self.assertRaisesMessage(ValueError, expected_message):
            models.CompositePrimaryKey("tenant_id", "id", editable=True)