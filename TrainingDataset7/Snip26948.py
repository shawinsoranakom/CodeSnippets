def test_alter_unique_together_fk_to_m2m(self):
        changes = self.get_changes(
            [self.author_name, self.book_unique_together],
            [
                self.author_name,
                ModelState(
                    "otherapp",
                    "Book",
                    [
                        ("id", models.AutoField(primary_key=True)),
                        ("author", models.ManyToManyField("testapp.Author")),
                        ("title", models.CharField(max_length=200)),
                    ],
                ),
            ],
        )
        self.assertNumberMigrations(changes, "otherapp", 1)
        self.assertOperationTypes(
            changes, "otherapp", 0, ["AlterUniqueTogether", "RemoveField", "AddField"]
        )
        self.assertOperationAttributes(
            changes, "otherapp", 0, 0, name="book", unique_together=set()
        )
        self.assertOperationAttributes(
            changes, "otherapp", 0, 1, model_name="book", name="author"
        )
        self.assertOperationAttributes(
            changes, "otherapp", 0, 2, model_name="book", name="author"
        )