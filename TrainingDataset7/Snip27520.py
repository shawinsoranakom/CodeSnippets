def test_create_model_add_field_not_through_m2m_through(self):
        """
        AddField should NOT optimize into CreateModel if it's an M2M using a
        through that's created between them.
        """
        self.assertDoesNotOptimize(
            [
                migrations.CreateModel("Employee", []),
                migrations.CreateModel("Employer", []),
                migrations.CreateModel(
                    "Employment",
                    [
                        (
                            "employee",
                            models.ForeignKey("migrations.Employee", models.CASCADE),
                        ),
                        (
                            "employment",
                            models.ForeignKey("migrations.Employer", models.CASCADE),
                        ),
                    ],
                ),
                migrations.AddField(
                    "Employer",
                    "employees",
                    models.ManyToManyField(
                        "migrations.Employee",
                        through="migrations.Employment",
                    ),
                ),
            ],
        )