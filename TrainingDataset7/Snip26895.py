def test_unmanaged_create(self):
        """The autodetector correctly deals with managed models."""
        # First, we test adding an unmanaged model
        changes = self.get_changes(
            [self.author_empty], [self.author_empty, self.author_unmanaged]
        )
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(changes, "testapp", 0, ["CreateModel"])
        self.assertOperationAttributes(
            changes, "testapp", 0, 0, name="AuthorUnmanaged", options={"managed": False}
        )