def test_repoint_field_m2m(self):
        project_state = self.set_up_test_model(
            "test_alflmm", second_model=True, third_model=True
        )

        project_state = self.apply_operations(
            "test_alflmm",
            project_state,
            operations=[
                migrations.AddField(
                    "Pony",
                    "places",
                    models.ManyToManyField("Stable", related_name="ponies"),
                )
            ],
        )
        Pony = project_state.apps.get_model("test_alflmm", "Pony")

        project_state = self.apply_operations(
            "test_alflmm",
            project_state,
            operations=[
                migrations.AlterField(
                    "Pony",
                    "places",
                    models.ManyToManyField(to="Van", related_name="ponies"),
                )
            ],
        )

        # Ensure the new field actually works
        Pony = project_state.apps.get_model("test_alflmm", "Pony")
        p = Pony.objects.create(pink=False, weight=4.55)
        p.places.create()
        self.assertEqual(p.places.count(), 1)
        p.places.all().delete()