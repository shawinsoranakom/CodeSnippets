def test_replaced_by_unexpired(self):
        c = ConfigOption(
            "mysection.oldName",
            description="My old description",
            replaced_by="mysection.newName",
            expiration_date="2100-01-01",
        )

        self.assertTrue(c.deprecated)
        self.assertFalse(c.is_expired())