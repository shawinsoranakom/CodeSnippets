def test_alter_field_to_not_null_with_db_default(self, mocked_ask_method):
        changes = self.get_changes(
            [self.author_name_null], [self.author_name_db_default]
        )
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(changes, "testapp", 0, ["AlterField"])
        self.assertOperationAttributes(
            changes, "testapp", 0, 0, name="name", preserve_default=True
        )
        self.assertOperationFieldAttributes(
            changes, "testapp", 0, 0, db_default="Ada Lovelace"
        )