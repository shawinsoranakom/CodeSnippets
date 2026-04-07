def test_add_blank_textfield_and_charfield(self, mocked_ask_method):
        """
        #23405 - Adding a NOT NULL and blank `CharField` or `TextField`
        without default should not prompt for a default.
        """
        changes = self.get_changes(
            [self.author_empty], [self.author_with_biography_blank]
        )
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(changes, "testapp", 0, ["AddField", "AddField"])
        self.assertOperationAttributes(changes, "testapp", 0, 0)