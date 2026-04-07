def test_rename_model_with_m2m_models_in_different_apps_with_same_name(self):
        app_label_1 = "test_rmw_m2m_1"
        app_label_2 = "test_rmw_m2m_2"
        project_state = self.apply_operations(
            app_label_1,
            ProjectState(),
            operations=[
                migrations.CreateModel(
                    "Rider",
                    fields=[
                        ("id", models.AutoField(primary_key=True)),
                    ],
                ),
            ],
        )
        project_state = self.apply_operations(
            app_label_2,
            project_state,
            operations=[
                migrations.CreateModel(
                    "Rider",
                    fields=[
                        ("id", models.AutoField(primary_key=True)),
                        ("riders", models.ManyToManyField(f"{app_label_1}.Rider")),
                    ],
                ),
            ],
        )
        m2m_table = f"{app_label_2}_rider_riders"
        self.assertColumnExists(m2m_table, "from_rider_id")
        self.assertColumnExists(m2m_table, "to_rider_id")

        Rider_1 = project_state.apps.get_model(app_label_1, "Rider")
        Rider_2 = project_state.apps.get_model(app_label_2, "Rider")
        rider_2 = Rider_2.objects.create()
        rider_2.riders.add(Rider_1.objects.create())
        # Rename model.
        project_state_2 = project_state.clone()
        project_state = self.apply_operations(
            app_label_2,
            project_state,
            operations=[migrations.RenameModel("Rider", "Pony")],
        )

        m2m_table = f"{app_label_2}_pony_riders"
        self.assertColumnExists(m2m_table, "pony_id")
        self.assertColumnExists(m2m_table, "rider_id")

        Rider_1 = project_state.apps.get_model(app_label_1, "Rider")
        Rider_2 = project_state.apps.get_model(app_label_2, "Pony")
        rider_2 = Rider_2.objects.create()
        rider_2.riders.add(Rider_1.objects.create())
        self.assertEqual(Rider_1.objects.count(), 2)
        self.assertEqual(Rider_2.objects.count(), 2)
        self.assertEqual(
            Rider_2._meta.get_field("riders").remote_field.through.objects.count(), 2
        )
        # Reversal.
        self.unapply_operations(
            app_label_2,
            project_state_2,
            operations=[migrations.RenameModel("Rider", "Pony")],
        )
        m2m_table = f"{app_label_2}_rider_riders"
        self.assertColumnExists(m2m_table, "to_rider_id")
        self.assertColumnExists(m2m_table, "from_rider_id")