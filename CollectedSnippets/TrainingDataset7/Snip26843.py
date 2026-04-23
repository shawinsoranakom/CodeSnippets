def test_fk_dependency(self):
        """Having a ForeignKey automatically adds a dependency."""
        # Note that testapp (author) has no dependencies,
        # otherapp (book) depends on testapp (author),
        # thirdapp (edition) depends on otherapp (book)
        changes = self.get_changes([], [self.author_name, self.book, self.edition])
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(changes, "testapp", 0, ["CreateModel"])
        self.assertOperationAttributes(changes, "testapp", 0, 0, name="Author")
        self.assertMigrationDependencies(changes, "testapp", 0, [])
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "otherapp", 1)
        self.assertOperationTypes(changes, "otherapp", 0, ["CreateModel"])
        self.assertOperationAttributes(changes, "otherapp", 0, 0, name="Book")
        self.assertMigrationDependencies(
            changes, "otherapp", 0, [("testapp", "auto_1")]
        )
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "thirdapp", 1)
        self.assertOperationTypes(changes, "thirdapp", 0, ["CreateModel"])
        self.assertOperationAttributes(changes, "thirdapp", 0, 0, name="Edition")
        self.assertMigrationDependencies(
            changes, "thirdapp", 0, [("otherapp", "auto_1")]
        )