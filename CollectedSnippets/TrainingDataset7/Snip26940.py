def test_bases_first_mixed_case_app_label(self):
        app_label = "MiXedCaseApp"
        changes = self.get_changes(
            [],
            [
                ModelState(
                    app_label,
                    "owner",
                    [
                        ("id", models.AutoField(primary_key=True)),
                    ],
                ),
                ModelState(
                    app_label,
                    "place",
                    [
                        ("id", models.AutoField(primary_key=True)),
                        (
                            "owner",
                            models.ForeignKey("MiXedCaseApp.owner", models.CASCADE),
                        ),
                    ],
                ),
                ModelState(app_label, "restaurant", [], bases=("MiXedCaseApp.place",)),
            ],
        )
        self.assertNumberMigrations(changes, app_label, 1)
        self.assertOperationTypes(
            changes,
            app_label,
            0,
            [
                "CreateModel",
                "CreateModel",
                "CreateModel",
            ],
        )
        self.assertOperationAttributes(changes, app_label, 0, 0, name="owner")
        self.assertOperationAttributes(changes, app_label, 0, 1, name="place")
        self.assertOperationAttributes(changes, app_label, 0, 2, name="restaurant")