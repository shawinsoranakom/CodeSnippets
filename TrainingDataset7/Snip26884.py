def test_create_model_and_unique_together(self):
        author = ModelState(
            "otherapp",
            "Author",
            [
                ("id", models.AutoField(primary_key=True)),
                ("name", models.CharField(max_length=200)),
            ],
        )
        book_with_author = ModelState(
            "otherapp",
            "Book",
            [
                ("id", models.AutoField(primary_key=True)),
                ("author", models.ForeignKey("otherapp.Author", models.CASCADE)),
                ("title", models.CharField(max_length=200)),
            ],
            {
                "unique_together": {("title", "author")},
            },
        )
        changes = self.get_changes(
            [self.book_with_no_author], [author, book_with_author]
        )
        # Right number of migrations?
        self.assertEqual(len(changes["otherapp"]), 1)
        # Right number of actions?
        migration = changes["otherapp"][0]
        self.assertEqual(len(migration.operations), 3)
        # Right actions order?
        self.assertOperationTypes(
            changes,
            "otherapp",
            0,
            ["CreateModel", "AddField", "AlterUniqueTogether"],
        )