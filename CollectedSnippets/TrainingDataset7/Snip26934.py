def test_set_alter_order_with_respect_to_index_constraint_unique_together(self):
        tests = [
            (
                "AddIndex",
                {
                    "indexes": [
                        models.Index(fields=["_order"], name="book_order_idx"),
                    ]
                },
            ),
            (
                "AddConstraint",
                {
                    "constraints": [
                        models.CheckConstraint(
                            condition=models.Q(_order__gt=1),
                            name="book_order_gt_1",
                        ),
                    ]
                },
            ),
            ("AlterUniqueTogether", {"unique_together": {("id", "_order")}}),
        ]
        for operation, extra_option in tests:
            with self.subTest(operation=operation):
                after = ModelState(
                    "testapp",
                    "Author",
                    [
                        ("id", models.AutoField(primary_key=True)),
                        ("name", models.CharField(max_length=200)),
                        ("book", models.ForeignKey("otherapp.Book", models.CASCADE)),
                    ],
                    options={
                        "order_with_respect_to": "book",
                        **extra_option,
                    },
                )
                changes = self.get_changes(
                    [self.book, self.author_with_book],
                    [self.book, after],
                )
                self.assertNumberMigrations(changes, "testapp", 1)
                self.assertOperationTypes(
                    changes,
                    "testapp",
                    0,
                    [
                        "AlterOrderWithRespectTo",
                        operation,
                    ],
                )