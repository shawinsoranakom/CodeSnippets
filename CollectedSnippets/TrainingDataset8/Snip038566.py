def test_replaced_by_expired(self):
        c = ConfigOption(
            "mysection.oldName",
            description="My old description",
            replaced_by="mysection.newName",
            expiration_date="2000-01-01",
        )

        self.assertTrue(c.deprecated)
        self.assertTrue(c.is_expired())