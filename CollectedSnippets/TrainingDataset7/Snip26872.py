def test_add_constraints_with_new_model(self):
        book_with_unique_title_and_pony = ModelState(
            "otherapp",
            "Book",
            [
                ("id", models.AutoField(primary_key=True)),
                ("title", models.CharField(max_length=200)),
                ("pony", models.ForeignKey("otherapp.Pony", models.CASCADE)),
            ],
            {
                "constraints": [
                    models.UniqueConstraint(
                        fields=["title", "pony"],
                        name="unique_title_pony",
                    )
                ]
            },
        )
        changes = self.get_changes(
            [self.book_with_no_author],
            [book_with_unique_title_and_pony, self.other_pony],
        )

        self.assertNumberMigrations(changes, "otherapp", 1)
        self.assertOperationTypes(
            changes,
            "otherapp",
            0,
            ["CreateModel", "AddField", "AddConstraint"],
        )