def test_fk_dependency_other_app(self):
        """
        #23100 - ForeignKeys correctly depend on other apps' models.
        """
        changes = self.get_changes(
            [self.author_name, self.book], [self.author_with_book, self.book]
        )
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(changes, "testapp", 0, ["AddField"])
        self.assertOperationAttributes(changes, "testapp", 0, 0, name="book")
        self.assertMigrationDependencies(
            changes, "testapp", 0, [("otherapp", "__first__")]
        )