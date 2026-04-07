def test_rename_field_reloads_state_on_fk_target_changes(self):
        """
        If RenameField doesn't reload state appropriately, the AlterField
        crashes on MySQL due to not dropping the PonyRider.pony foreign key
        constraint before modifying the column.
        """
        app_label = "alter_rename_field_reloads_state_on_fk_target_changes"
        project_state = self.apply_operations(
            app_label,
            ProjectState(),
            operations=[
                migrations.CreateModel(
                    "Rider",
                    fields=[
                        ("id", models.CharField(primary_key=True, max_length=100)),
                    ],
                ),
                migrations.CreateModel(
                    "Pony",
                    fields=[
                        ("id", models.CharField(primary_key=True, max_length=100)),
                        (
                            "rider",
                            models.ForeignKey("%s.Rider" % app_label, models.CASCADE),
                        ),
                    ],
                ),
                migrations.CreateModel(
                    "PonyRider",
                    fields=[
                        ("id", models.AutoField(primary_key=True)),
                        (
                            "pony",
                            models.ForeignKey("%s.Pony" % app_label, models.CASCADE),
                        ),
                    ],
                ),
            ],
        )
        project_state = self.apply_operations(
            app_label,
            project_state,
            operations=[
                migrations.RenameField("Rider", "id", "id2"),
                migrations.AlterField(
                    "Pony", "id", models.CharField(primary_key=True, max_length=99)
                ),
            ],
        )