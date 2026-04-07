def test_same_app_circular_fk_dependency_with_unique_together_and_indexes(self):
        """
        #22275 - A migration with circular FK dependency does not try
        to create unique together constraint and indexes before creating all
        required fields first.
        """
        changes = self.get_changes([], [self.knight, self.rabbit])
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "eggs", 1)
        self.assertOperationTypes(
            changes,
            "eggs",
            0,
            ["CreateModel", "CreateModel"],
        )
        self.assertNotIn("unique_together", changes["eggs"][0].operations[0].options)
        self.assertMigrationDependencies(changes, "eggs", 0, [])