def test_remove_composite_pk(self):
        before = [
            ModelState(
                "app",
                "foo",
                [
                    ("pk", models.CompositePrimaryKey("foo_id", "bar_id")),
                    ("id", models.IntegerField()),
                ],
            ),
        ]
        after = [
            ModelState(
                "app",
                "foo",
                [
                    ("id", models.AutoField(primary_key=True)),
                ],
            ),
        ]

        changes = self.get_changes(before, after)
        self.assertNumberMigrations(changes, "app", 1)
        self.assertOperationTypes(changes, "app", 0, ["RemoveField", "AlterField"])
        self.assertOperationAttributes(
            changes,
            "app",
            0,
            0,
            name="pk",
            model_name="foo",
        )
        self.assertOperationAttributes(
            changes,
            "app",
            0,
            1,
            name="id",
            model_name="foo",
            preserve_default=True,
        )