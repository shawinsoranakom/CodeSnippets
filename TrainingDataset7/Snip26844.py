def test_proxy_fk_dependency(self):
        """FK dependencies still work on proxy models."""
        # Note that testapp (author) has no dependencies,
        # otherapp (book) depends on testapp (authorproxy)
        changes = self.get_changes(
            [], [self.author_empty, self.author_proxy_third, self.book_proxy_fk]
        )
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
            changes, "otherapp", 0, [("thirdapp", "auto_1")]
        )
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "thirdapp", 1)
        self.assertOperationTypes(changes, "thirdapp", 0, ["CreateModel"])
        self.assertOperationAttributes(changes, "thirdapp", 0, 0, name="AuthorProxy")
        self.assertMigrationDependencies(
            changes, "thirdapp", 0, [("testapp", "auto_1")]
        )