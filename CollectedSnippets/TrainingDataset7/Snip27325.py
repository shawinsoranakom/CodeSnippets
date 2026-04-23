def test_rename_model_with_self_referential_m2m(self):
        app_label = "test_rename_model_with_self_referential_m2m"

        project_state = self.apply_operations(
            app_label,
            ProjectState(),
            operations=[
                migrations.CreateModel(
                    "ReflexivePony",
                    fields=[
                        ("id", models.AutoField(primary_key=True)),
                        ("ponies", models.ManyToManyField("self")),
                    ],
                ),
            ],
        )
        project_state = self.apply_operations(
            app_label,
            project_state,
            operations=[
                migrations.RenameModel("ReflexivePony", "ReflexivePony2"),
            ],
        )
        Pony = project_state.apps.get_model(app_label, "ReflexivePony2")
        pony = Pony.objects.create()
        pony.ponies.add(pony)