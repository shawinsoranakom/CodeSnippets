def test_alter_fk_before_model_deletion(self):
        """
        ForeignKeys are altered _before_ the model they used to
        refer to are deleted.
        """
        changes = self.get_changes(
            [self.author_name, self.publisher_with_author],
            [self.aardvark_testapp, self.publisher_with_aardvark_author],
        )
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(
            changes, "testapp", 0, ["CreateModel", "AlterField", "DeleteModel"]
        )
        self.assertOperationAttributes(changes, "testapp", 0, 0, name="Aardvark")
        self.assertOperationAttributes(changes, "testapp", 0, 1, name="author")
        self.assertOperationAttributes(changes, "testapp", 0, 2, name="Author")