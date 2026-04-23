def test_rename_model_with_m2m(self):
        app_label = "test_rename_model_with_m2m"
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
                        ("riders", models.ManyToManyField("Rider")),
                    ],
                ),
            ],
        )
        Pony = project_state.apps.get_model(app_label, "Pony")
        Rider = project_state.apps.get_model(app_label, "Rider")
        pony = Pony.objects.create()
        rider = Rider.objects.create()
        pony.riders.add(rider)

        project_state = self.apply_operations(
            app_label,
            project_state,
            operations=[
                migrations.RenameModel("Pony", "Pony2"),
            ],
        )
        Pony = project_state.apps.get_model(app_label, "Pony2")
        Rider = project_state.apps.get_model(app_label, "Rider")
        pony = Pony.objects.create()
        rider = Rider.objects.create()
        pony.riders.add(rider)
        self.assertEqual(Pony.objects.count(), 2)
        self.assertEqual(Rider.objects.count(), 2)
        self.assertEqual(
            Pony._meta.get_field("riders").remote_field.through.objects.count(), 2
        )