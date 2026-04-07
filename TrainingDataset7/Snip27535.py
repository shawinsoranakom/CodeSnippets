def test_optimize_elidable_operation(self):
        elidable_operation = operations.base.Operation()
        elidable_operation.elidable = True
        self.assertOptimizesTo(
            [
                elidable_operation,
                migrations.CreateModel(
                    "Foo", [("name", models.CharField(max_length=255))]
                ),
                elidable_operation,
                migrations.CreateModel("Bar", [("size", models.IntegerField())]),
                elidable_operation,
                migrations.RenameModel("Foo", "Phou"),
                migrations.DeleteModel("Bar"),
                elidable_operation,
            ],
            [
                migrations.CreateModel(
                    "Phou", [("name", models.CharField(max_length=255))]
                ),
            ],
        )