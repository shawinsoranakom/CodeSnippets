def test_m2m_w_through_multistep_remove(self):
        """
        A model with a m2m field that specifies a "through" model cannot be
        removed in the same migration as that through model as the schema will
        pass through an inconsistent state. The autodetector should produce two
        migrations to avoid this issue.
        """
        changes = self.get_changes(
            [self.author_with_m2m_through, self.publisher, self.contract],
            [self.publisher],
        )
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(
            changes,
            "testapp",
            0,
            ["RemoveField", "RemoveField", "DeleteModel", "DeleteModel"],
        )
        self.assertOperationAttributes(
            changes, "testapp", 0, 0, name="author", model_name="contract"
        )
        self.assertOperationAttributes(
            changes, "testapp", 0, 1, name="publisher", model_name="contract"
        )
        self.assertOperationAttributes(changes, "testapp", 0, 2, name="Author")
        self.assertOperationAttributes(changes, "testapp", 0, 3, name="Contract")