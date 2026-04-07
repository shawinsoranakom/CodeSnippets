def test_add_model_no_relations(self):
        project_state = ProjectState()
        project_state.add_model(
            ModelState(
                app_label="migrations",
                name="Tag",
                fields=[("id", models.AutoField(primary_key=True))],
            )
        )
        self.assertEqual(project_state.relations, {})