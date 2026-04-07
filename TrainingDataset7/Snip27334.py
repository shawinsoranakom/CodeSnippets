def test_add_generated_field(self):
        app_label = "test_add_generated_field"
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
                        ("name", models.CharField(max_length=20)),
                        (
                            "rider",
                            models.ForeignKey(
                                f"{app_label}.Rider", on_delete=models.CASCADE
                            ),
                        ),
                        (
                            "name_and_id",
                            models.GeneratedField(
                                expression=Concat(("name"), ("rider_id")),
                                output_field=models.CharField(max_length=60),
                                db_persist=True,
                            ),
                        ),
                    ],
                ),
            ],
        )
        Pony = project_state.apps.get_model(app_label, "Pony")
        Rider = project_state.apps.get_model(app_label, "Rider")
        rider = Rider.objects.create()
        pony = Pony.objects.create(name="pony", rider=rider)
        self.assertEqual(pony.name_and_id, str(pony.name) + str(rider.id))

        new_rider = Rider.objects.create()
        pony.rider = new_rider
        pony.save()
        pony.refresh_from_db()
        self.assertEqual(pony.name_and_id, str(pony.name) + str(new_rider.id))