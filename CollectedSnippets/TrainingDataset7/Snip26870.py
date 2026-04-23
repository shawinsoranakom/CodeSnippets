def test_create_model_with_check_constraint(self):
        """Test creation of new model with constraints already defined."""
        author = ModelState(
            "otherapp",
            "Author",
            [
                ("id", models.AutoField(primary_key=True)),
                ("name", models.CharField(max_length=200)),
            ],
            {
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(name__contains="Bob"),
                        name="name_contains_bob",
                    )
                ]
            },
        )
        changes = self.get_changes([], [author])
        constraint = models.CheckConstraint(
            condition=models.Q(name__contains="Bob"), name="name_contains_bob"
        )
        # Right number of migrations?
        self.assertEqual(len(changes["otherapp"]), 1)
        # Right number of actions?
        migration = changes["otherapp"][0]
        self.assertEqual(len(migration.operations), 1)
        # Right actions order?
        self.assertOperationTypes(changes, "otherapp", 0, ["CreateModel"])
        self.assertOperationAttributes(
            changes,
            "otherapp",
            0,
            0,
            name="Author",
            options={"constraints": [constraint]},
        )