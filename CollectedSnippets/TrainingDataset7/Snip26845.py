def test_same_app_no_fk_dependency(self):
        """
        A migration with a FK between two models of the same app
        does not have a dependency to itself.
        """
        changes = self.get_changes([], [self.author_with_publisher, self.publisher])
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(changes, "testapp", 0, ["CreateModel", "CreateModel"])
        self.assertOperationAttributes(changes, "testapp", 0, 0, name="Publisher")
        self.assertOperationAttributes(changes, "testapp", 0, 1, name="Author")
        self.assertMigrationDependencies(changes, "testapp", 0, [])