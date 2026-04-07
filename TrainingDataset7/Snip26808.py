def test_add_not_null_field_with_db_default(self, mocked_ask_method):
        changes = self.get_changes([self.author_empty], [self.author_name_db_default])
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(changes, "testapp", 0, ["AddField"])
        self.assertOperationAttributes(
            changes, "testapp", 0, 0, name="name", preserve_default=True
        )
        self.assertOperationFieldAttributes(
            changes, "testapp", 0, 0, db_default="Ada Lovelace"
        )