def test_add_model_order_with_respect_to_constraint(self):
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
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(_order__gt=1), name="book_order_gt_1"
                    ),
                ],
            },
        )
        changes = self.get_changes([], [self.book, after])
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(
            changes,
            "testapp",
            0,
            ["CreateModel"],
        )
        self.assertOperationAttributes(
            changes,
            "testapp",
            0,
            0,
            name="Author",
            options={
                "order_with_respect_to": "book",
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(_order__gt=1), name="book_order_gt_1"
                    )
                ],
            },
        )