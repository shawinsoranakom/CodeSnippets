def test_non_circular_foreignkey_dependency_removal(self):
        """
        If two models with a ForeignKey from one to the other are removed at
        the same time, the autodetector should remove them in the correct
        order.
        """
        changes = self.get_changes(
            [self.author_with_publisher, self.publisher_with_author], []
        )
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(
            changes, "testapp", 0, ["RemoveField", "DeleteModel", "DeleteModel"]
        )
        self.assertOperationAttributes(
            changes, "testapp", 0, 0, name="author", model_name="publisher"
        )
        self.assertOperationAttributes(changes, "testapp", 0, 1, name="Author")
        self.assertOperationAttributes(changes, "testapp", 0, 2, name="Publisher")