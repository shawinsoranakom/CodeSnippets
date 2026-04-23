def test_add_composite_pk(self, mocked_ask_method):
        before = [
            ModelState(
                "app",
                "foo",
                [
                    ("id", models.AutoField(primary_key=True)),
                ],
            ),
        ]
        after = [
            ModelState(
                "app",
                "foo",
                [
                    ("pk", models.CompositePrimaryKey("foo_id", "bar_id")),
                    ("id", models.IntegerField()),
                ],
            ),
        ]

        changes = self.get_changes(before, after)
        self.assertEqual(mocked_ask_method.call_count, 0)
        self.assertNumberMigrations(changes, "app", 1)
        self.assertOperationTypes(changes, "app", 0, ["AddField", "AlterField"])
        self.assertOperationAttributes(
            changes,
            "app",
            0,
            0,
            name="pk",
            model_name="foo",
            preserve_default=True,
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