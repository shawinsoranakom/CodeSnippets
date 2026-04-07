def test_create_model_with_indexes(self):
        """Test creation of new model with indexes already defined."""
        added_index = models.Index(
            fields=["name"], name="create_model_with_indexes_idx"
        )
        author = ModelState(
            "otherapp",
            "Author",
            [
                ("id", models.AutoField(primary_key=True)),
                ("name", models.CharField(max_length=200)),
            ],
            {
                "indexes": [added_index],
            },
        )
        changes = self.get_changes([], [author])
        # Right number of migrations?
        self.assertEqual(len(changes["otherapp"]), 1)
        # Right number of actions?
        migration = changes["otherapp"][0]
        self.assertEqual(len(migration.operations), 1)
        # Right actions order?
        self.assertOperationTypes(changes, "otherapp", 0, ["CreateModel"])
        self.assertOperationAttributes(changes, "otherapp", 0, 0, name="Author")
        self.assertOperationAttributes(
            changes,
            "otherapp",
            0,
            0,
            name="Author",
            options={"indexes": [added_index]},
        )