def test_alter_field_to_not_null_with_default(self, mocked_ask_method):
        """
        #23609 - Tests autodetection of nullable to non-nullable alterations.
        """
        changes = self.get_changes([self.author_name_null], [self.author_name_default])
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(changes, "testapp", 0, ["AlterField"])
        self.assertOperationAttributes(
            changes, "testapp", 0, 0, name="name", preserve_default=True
        )
        self.assertOperationFieldAttributes(
            changes, "testapp", 0, 0, default="Ada Lovelace"
        )