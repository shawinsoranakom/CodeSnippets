def test_rename_m2m_through_model(self):
        app_label = "test_rename_through"
        project_state = self.apply_operations(
            app_label,
            ProjectState(),
            operations=[
                migrations.CreateModel(
                    "Rider",
                    fields=[
                        ("id", models.AutoField(primary_key=True)),
                    ],
                ),
                migrations.CreateModel(
                    "Pony",
                    fields=[
                        ("id", models.AutoField(primary_key=True)),
                    ],
                ),
                migrations.CreateModel(
                    "PonyRider",
                    fields=[
                        ("id", models.AutoField(primary_key=True)),
                        (
                            "rider",
                            models.ForeignKey(
                                "test_rename_through.Rider", models.CASCADE
                            ),
                        ),
                        (
                            "pony",
                            models.ForeignKey(
                                "test_rename_through.Pony", models.CASCADE
                            ),
                        ),
                    ],
                ),
                migrations.AddField(
                    "Pony",
                    "riders",
                    models.ManyToManyField(
                        "test_rename_through.Rider",
                        through="test_rename_through.PonyRider",
                    ),
                ),
            ],
        )
        Pony = project_state.apps.get_model(app_label, "Pony")
        Rider = project_state.apps.get_model(app_label, "Rider")
        PonyRider = project_state.apps.get_model(app_label, "PonyRider")
        pony = Pony.objects.create()
        rider = Rider.objects.create()
        PonyRider.objects.create(pony=pony, rider=rider)

        project_state = self.apply_operations(
            app_label,
            project_state,
            operations=[
                migrations.RenameModel("PonyRider", "PonyRider2"),
            ],
        )
        Pony = project_state.apps.get_model(app_label, "Pony")
        Rider = project_state.apps.get_model(app_label, "Rider")
        PonyRider = project_state.apps.get_model(app_label, "PonyRider2")
        pony = Pony.objects.first()
        rider = Rider.objects.create()
        PonyRider.objects.create(pony=pony, rider=rider)
        self.assertEqual(Pony.objects.count(), 1)
        self.assertEqual(Rider.objects.count(), 2)
        self.assertEqual(PonyRider.objects.count(), 2)
        self.assertEqual(pony.riders.count(), 2)