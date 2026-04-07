def test_rename_indexes(self):
        book_renamed_indexes = ModelState(
            "otherapp",
            "Book",
            [
                ("id", models.AutoField(primary_key=True)),
                ("author", models.ForeignKey("testapp.Author", models.CASCADE)),
                ("title", models.CharField(max_length=200)),
            ],
            {
                "indexes": [
                    models.Index(
                        fields=["author", "title"], name="renamed_book_title_author_idx"
                    )
                ],
            },
        )
        changes = self.get_changes(
            [self.author_empty, self.book_indexes],
            [self.author_empty, book_renamed_indexes],
        )
        self.assertNumberMigrations(changes, "otherapp", 1)
        self.assertOperationTypes(changes, "otherapp", 0, ["RenameIndex"])
        self.assertOperationAttributes(
            changes,
            "otherapp",
            0,
            0,
            model_name="book",
            new_name="renamed_book_title_author_idx",
            old_name="book_title_author_idx",
        )