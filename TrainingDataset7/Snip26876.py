def test_remove_constraints(self):
        """Test change detection of removed constraints."""
        changes = self.get_changes(
            [self.author_name_check_constraint], [self.author_name]
        )
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(changes, "testapp", 0, ["RemoveConstraint"])
        self.assertOperationAttributes(
            changes, "testapp", 0, 0, model_name="author", name="name_contains_bob"
        )