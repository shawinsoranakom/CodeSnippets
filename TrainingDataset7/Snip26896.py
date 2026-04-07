def test_unmanaged_delete(self):
        changes = self.get_changes(
            [self.author_empty, self.author_unmanaged], [self.author_empty]
        )
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(changes, "testapp", 0, ["DeleteModel"])