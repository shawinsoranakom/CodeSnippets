def test_reload_related_model_on_non_relational_fields(self):
        """
        The model is reloaded even on changes that are not involved in
        relations. Other models pointing to or from it are also reloaded.
        """
        project_state = ProjectState()
        project_state.apps  # Render project state.
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
                    ("name", models.TextField()),
                ],
            )
        )
        project_state.add_model(
            ModelState(
                "migrations",
                "D",
                [
                    ("a", models.ForeignKey("A", models.CASCADE)),
                ],
            )
        )
        operation = AlterField(
            model_name="C",
            name="name",
            field=models.TextField(blank=True),
        )
        operation.state_forwards("migrations", project_state)
        project_state.reload_model("migrations", "a", delay=True)
        A = project_state.apps.get_model("migrations.A")
        B = project_state.apps.get_model("migrations.B")
        D = project_state.apps.get_model("migrations.D")
        self.assertIs(B._meta.get_field("a").related_model, A)
        self.assertIs(D._meta.get_field("a").related_model, A)