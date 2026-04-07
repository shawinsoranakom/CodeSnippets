def test_bases_first(self):
        """Bases of other models come first."""
        changes = self.get_changes(
            [], [self.aardvark_based_on_author, self.author_name]
        )
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(changes, "testapp", 0, ["CreateModel", "CreateModel"])
        self.assertOperationAttributes(changes, "testapp", 0, 0, name="Author")
        self.assertOperationAttributes(changes, "testapp", 0, 1, name="Aardvark")