def test_alter_field_to_fk_dependency_other_app(self):
        changes = self.get_changes(
            [self.author_empty, self.book_with_no_author_fk],
            [self.author_empty, self.book],
        )
        self.assertNumberMigrations(changes, "otherapp", 1)
        self.assertOperationTypes(changes, "otherapp", 0, ["AlterField"])
        self.assertMigrationDependencies(
            changes, "otherapp", 0, [("testapp", "__first__")]
        )