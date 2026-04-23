def test_rename_m2m_model_after_rename_field(self):
        """RenameModel renames a many-to-many column after a RenameField."""
        app_label = "test_rename_multiple"
        project_state = self.apply_operations(
            app_label,
            ProjectState(),
            operations=[
                migrations.CreateModel(
                    "Pony",
                    fields=[
                        ("id", models.AutoField(primary_key=True)),
                        ("name", models.CharField(max_length=20)),
                    ],
                ),
                migrations.CreateModel(
                    "Rider",
                    fields=[
                        ("id", models.AutoField(primary_key=True)),
                        (
                            "pony",
                            models.ForeignKey(
                                "test_rename_multiple.Pony", models.CASCADE
                            ),
                        ),
                    ],
                ),
                migrations.CreateModel(
                    "PonyRider",
                    fields=[
                        ("id", models.AutoField(primary_key=True)),
                        ("riders", models.ManyToManyField("Rider")),
                    ],
                ),
                migrations.RenameField(
                    model_name="pony", old_name="name", new_name="fancy_name"
                ),
                migrations.RenameModel(old_name="Rider", new_name="Jockey"),
            ],
        )
        Pony = project_state.apps.get_model(app_label, "Pony")
        Jockey = project_state.apps.get_model(app_label, "Jockey")
        PonyRider = project_state.apps.get_model(app_label, "PonyRider")
        # No "no such column" error means the column was renamed correctly.
        pony = Pony.objects.create(fancy_name="a good name")
        jockey = Jockey.objects.create(pony=pony)
        ponyrider = PonyRider.objects.create()
        ponyrider.riders.add(jockey)