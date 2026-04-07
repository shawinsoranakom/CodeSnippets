def test_many_to_many_changed_to_concrete_field(self):
        """
        #23938 - Changing a ManyToManyField into a concrete field
        first removes the m2m field and then adds the concrete field.
        """
        changes = self.get_changes(
            [self.author_with_m2m, self.publisher], [self.author_with_former_m2m]
        )
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(
            changes, "testapp", 0, ["RemoveField", "DeleteModel", "AddField"]
        )
        self.assertOperationAttributes(
            changes, "testapp", 0, 0, name="publishers", model_name="author"
        )
        self.assertOperationAttributes(changes, "testapp", 0, 1, name="Publisher")
        self.assertOperationAttributes(
            changes, "testapp", 0, 2, name="publishers", model_name="author"
        )
        self.assertOperationFieldAttributes(changes, "testapp", 0, 2, max_length=100)