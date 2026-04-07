def test_set_alter_order_with_respect_to(self):
        """Setting order_with_respect_to adds a field."""
        changes = self.get_changes(
            [self.book, self.author_with_book],
            [self.book, self.author_with_book_order_wrt],
        )
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(changes, "testapp", 0, ["AlterOrderWithRespectTo"])
        self.assertOperationAttributes(
            changes, "testapp", 0, 0, name="author", order_with_respect_to="book"
        )