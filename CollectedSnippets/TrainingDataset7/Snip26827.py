def test_foreign_object_from_to_fields_list(self):
        author_state = ModelState(
            "app",
            "Author",
            [("id", models.AutoField(primary_key=True))],
        )
        book_state = ModelState(
            "app",
            "Book",
            [
                ("id", models.AutoField(primary_key=True)),
                ("name", models.CharField()),
                ("author_id", models.IntegerField()),
                (
                    "author",
                    models.ForeignObject(
                        "app.Author",
                        models.CASCADE,
                        from_fields=["author_id"],
                        to_fields=["id"],
                    ),
                ),
            ],
        )
        book_state_copy = copy.deepcopy(book_state)
        changes = self.get_changes(
            [author_state, book_state],
            [author_state, book_state_copy],
        )
        self.assertEqual(changes, {})