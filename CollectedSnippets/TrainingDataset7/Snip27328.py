def test_rename_model_with_db_table_rename_m2m(self):
        app_label = "test_rmwdbrm2m"
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
                    options={"db_table": "pony"},
                ),
            ],
        )
        new_state = self.apply_operations(
            app_label,
            project_state,
            operations=[migrations.RenameModel("Pony", "PinkPony")],
        )
        Pony = new_state.apps.get_model(app_label, "PinkPony")
        Rider = new_state.apps.get_model(app_label, "Rider")
        pony = Pony.objects.create()
        rider = Rider.objects.create()
        pony.riders.add(rider)