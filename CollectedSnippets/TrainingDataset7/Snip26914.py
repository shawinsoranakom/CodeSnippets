def test_add_many_to_many(self, mocked_ask_method):
        """
        #22435 - Adding a ManyToManyField should not prompt for a default.
        """
        changes = self.get_changes(
            [self.author_empty, self.publisher], [self.author_with_m2m, self.publisher]
        )
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(changes, "testapp", 0, ["AddField"])
        self.assertOperationAttributes(changes, "testapp", 0, 0, name="publishers")