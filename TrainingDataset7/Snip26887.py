def test_partly_alter_unique_together_increase(self):
        initial_author = ModelState(
            "testapp",
            "Author",
            [
                ("id", models.AutoField(primary_key=True)),
                ("name", models.CharField(max_length=200)),
                ("age", models.IntegerField()),
            ],
            {
                "unique_together": {("name",)},
            },
        )
        author_new_constraints = ModelState(
            "testapp",
            "Author",
            [
                ("id", models.AutoField(primary_key=True)),
                ("name", models.CharField(max_length=200)),
                ("age", models.IntegerField()),
            ],
            {
                "unique_together": {("name",), ("age",)},
            },
        )
        changes = self.get_changes([initial_author], [author_new_constraints])

        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(
            changes,
            "testapp",
            0,
            ["AlterUniqueTogether"],
        )
        self.assertOperationAttributes(
            changes,
            "testapp",
            0,
            0,
            name="author",
            unique_together={("name",), ("age",)},
        )