def test_constraint_dropped_and_recreated(self):
        altered_constraint = models.CheckConstraint(
            condition=models.Q(name__contains="bob"),
            name="name_contains_bob",
        )
        author_name_check_constraint_lowercased = copy.deepcopy(
            self.author_name_check_constraint
        )
        author_name_check_constraint_lowercased.options = {
            "constraints": [altered_constraint]
        }
        changes = self.get_changes(
            [self.author_name_check_constraint],
            [author_name_check_constraint_lowercased],
        )

        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(
            changes, "testapp", 0, ["RemoveConstraint", "AddConstraint"]
        )
        self.assertOperationAttributes(
            changes,
            "testapp",
            0,
            0,
            model_name="author",
            name="name_contains_bob",
        )
        self.assertOperationAttributes(
            changes,
            "testapp",
            0,
            1,
            model_name="author",
            constraint=altered_constraint,
        )