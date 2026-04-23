def test_add_model_order_with_respect_to(self):
        """
        Setting order_with_respect_to when adding the whole model
        does things in the right order.
        """
        changes = self.get_changes([], [self.book, self.author_with_book_order_wrt])
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(changes, "testapp", 0, ["CreateModel"])
        self.assertOperationAttributes(
            changes,
            "testapp",
            0,
            0,
            name="Author",
            options={"order_with_respect_to": "book"},
        )
        self.assertNotIn(
            "_order",
            [name for name, field in changes["testapp"][0].operations[0].fields],
        )