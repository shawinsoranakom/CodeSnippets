def test_remove_alter_order_with_respect_to(self):
        """
        Removing order_with_respect_to when removing the FK too does
        things in the right order.
        """
        changes = self.get_changes(
            [self.book, self.author_with_book_order_wrt], [self.author_name]
        )
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(
            changes, "testapp", 0, ["AlterOrderWithRespectTo", "RemoveField"]
        )
        self.assertOperationAttributes(
            changes, "testapp", 0, 0, name="author", order_with_respect_to=None
        )
        self.assertOperationAttributes(
            changes, "testapp", 0, 1, model_name="author", name="book"
        )