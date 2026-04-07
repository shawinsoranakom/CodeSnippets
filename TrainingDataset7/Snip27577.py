def test_reload_model_relationship_consistency(self):
        project_state = ProjectState()
        project_state.add_model(ModelState("migrations", "A", []))
        project_state.add_model(
            ModelState(
                "migrations",
                "B",
                [
                    ("a", models.ForeignKey("A", models.CASCADE)),
                ],
            )
        )
        project_state.add_model(
            ModelState(
                "migrations",
                "C",
                [
                    ("b", models.ForeignKey("B", models.CASCADE)),
                ],
            )
        )
        A = project_state.apps.get_model("migrations.A")
        B = project_state.apps.get_model("migrations.B")
        C = project_state.apps.get_model("migrations.C")
        self.assertEqual([r.related_model for r in A._meta.related_objects], [B])
        self.assertEqual([r.related_model for r in B._meta.related_objects], [C])
        self.assertEqual([r.related_model for r in C._meta.related_objects], [])

        project_state.reload_model("migrations", "a", delay=True)
        A = project_state.apps.get_model("migrations.A")
        B = project_state.apps.get_model("migrations.B")
        C = project_state.apps.get_model("migrations.C")
        self.assertEqual([r.related_model for r in A._meta.related_objects], [B])
        self.assertEqual([r.related_model for r in B._meta.related_objects], [C])
        self.assertEqual([r.related_model for r in C._meta.related_objects], [])