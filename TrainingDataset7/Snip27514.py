def test_optimize_through_create(self):
        """
        We should be able to optimize away create/delete through a create or
        delete of a different model, but only if the create operation does not
        mention the model at all.
        """
        # These should work
        self.assertOptimizesTo(
            [
                migrations.CreateModel(
                    "Foo", [("name", models.CharField(max_length=255))]
                ),
                migrations.CreateModel("Bar", [("size", models.IntegerField())]),
                migrations.DeleteModel("Foo"),
            ],
            [
                migrations.CreateModel("Bar", [("size", models.IntegerField())]),
            ],
        )
        self.assertOptimizesTo(
            [
                migrations.CreateModel(
                    "Foo", [("name", models.CharField(max_length=255))]
                ),
                migrations.CreateModel("Bar", [("size", models.IntegerField())]),
                migrations.DeleteModel("Bar"),
                migrations.DeleteModel("Foo"),
            ],
            [],
        )
        self.assertOptimizesTo(
            [
                migrations.CreateModel(
                    "Foo", [("name", models.CharField(max_length=255))]
                ),
                migrations.CreateModel("Bar", [("size", models.IntegerField())]),
                migrations.DeleteModel("Foo"),
                migrations.DeleteModel("Bar"),
            ],
            [],
        )
        # Operations should be optimized if the FK references a model from the
        # other app.
        self.assertOptimizesTo(
            [
                migrations.CreateModel(
                    "Foo", [("name", models.CharField(max_length=255))]
                ),
                migrations.CreateModel(
                    "Bar", [("other", models.ForeignKey("testapp.Foo", models.CASCADE))]
                ),
                migrations.DeleteModel("Foo"),
            ],
            [
                migrations.CreateModel(
                    "Bar", [("other", models.ForeignKey("testapp.Foo", models.CASCADE))]
                ),
            ],
            app_label="otherapp",
        )
        # But it shouldn't work if a FK references a model with the same
        # app_label.
        self.assertDoesNotOptimize(
            [
                migrations.CreateModel(
                    "Foo", [("name", models.CharField(max_length=255))]
                ),
                migrations.CreateModel(
                    "Bar", [("other", models.ForeignKey("Foo", models.CASCADE))]
                ),
                migrations.DeleteModel("Foo"),
            ],
        )
        self.assertDoesNotOptimize(
            [
                migrations.CreateModel(
                    "Foo", [("name", models.CharField(max_length=255))]
                ),
                migrations.CreateModel(
                    "Bar", [("other", models.ForeignKey("testapp.Foo", models.CASCADE))]
                ),
                migrations.DeleteModel("Foo"),
            ],
            app_label="testapp",
        )
        # This should not work - bases should block it
        self.assertDoesNotOptimize(
            [
                migrations.CreateModel(
                    "Foo", [("name", models.CharField(max_length=255))]
                ),
                migrations.CreateModel(
                    "Bar", [("size", models.IntegerField())], bases=("Foo",)
                ),
                migrations.DeleteModel("Foo"),
            ],
        )
        self.assertDoesNotOptimize(
            [
                migrations.CreateModel(
                    "Foo", [("name", models.CharField(max_length=255))]
                ),
                migrations.CreateModel(
                    "Bar", [("size", models.IntegerField())], bases=("testapp.Foo",)
                ),
                migrations.DeleteModel("Foo"),
            ],
            app_label="testapp",
        )
        # The same operations should be optimized if app_label and none of
        # bases belong to that app.
        self.assertOptimizesTo(
            [
                migrations.CreateModel(
                    "Foo", [("name", models.CharField(max_length=255))]
                ),
                migrations.CreateModel(
                    "Bar", [("size", models.IntegerField())], bases=("testapp.Foo",)
                ),
                migrations.DeleteModel("Foo"),
            ],
            [
                migrations.CreateModel(
                    "Bar", [("size", models.IntegerField())], bases=("testapp.Foo",)
                ),
            ],
            app_label="otherapp",
        )
        # But it shouldn't work if some of bases belongs to the specified app.
        self.assertDoesNotOptimize(
            [
                migrations.CreateModel(
                    "Foo", [("name", models.CharField(max_length=255))]
                ),
                migrations.CreateModel(
                    "Bar", [("size", models.IntegerField())], bases=("testapp.Foo",)
                ),
                migrations.DeleteModel("Foo"),
            ],
            app_label="testapp",
        )

        self.assertOptimizesTo(
            [
                migrations.CreateModel(
                    "Book", [("name", models.CharField(max_length=255))]
                ),
                migrations.CreateModel(
                    "Person", [("name", models.CharField(max_length=255))]
                ),
                migrations.AddField(
                    "book",
                    "author",
                    models.ForeignKey("test_app.Person", models.CASCADE),
                ),
                migrations.CreateModel(
                    "Review",
                    [("book", models.ForeignKey("test_app.Book", models.CASCADE))],
                ),
                migrations.CreateModel(
                    "Reviewer", [("name", models.CharField(max_length=255))]
                ),
                migrations.AddField(
                    "review",
                    "reviewer",
                    models.ForeignKey("test_app.Reviewer", models.CASCADE),
                ),
                migrations.RemoveField("book", "author"),
                migrations.DeleteModel("Person"),
            ],
            [
                migrations.CreateModel(
                    "Book", [("name", models.CharField(max_length=255))]
                ),
                migrations.CreateModel(
                    "Reviewer", [("name", models.CharField(max_length=255))]
                ),
                migrations.CreateModel(
                    "Review",
                    [
                        ("book", models.ForeignKey("test_app.Book", models.CASCADE)),
                        (
                            "reviewer",
                            models.ForeignKey("test_app.Reviewer", models.CASCADE),
                        ),
                    ],
                ),
            ],
            app_label="test_app",
        )