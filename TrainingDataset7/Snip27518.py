def test_create_model_no_reordering_for_unrelated_fk(self):
        """
        CreateModel order remains unchanged if the later AddField operation
        isn't a FK between them.
        """
        self.assertDoesNotOptimize(
            [
                migrations.CreateModel(
                    "Foo", [("name", models.CharField(max_length=255))]
                ),
                migrations.CreateModel("Link", [("url", models.TextField())]),
                migrations.AddField(
                    "Other",
                    "link",
                    models.ForeignKey("migrations.Link", models.CASCADE),
                ),
            ],
        )