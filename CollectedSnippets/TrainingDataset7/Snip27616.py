def test_repr(self):
        field = models.CharField(max_length=1)
        state = ModelState(
            "app", "Model", [("name", field)], bases=["app.A", "app.B", "app.C"]
        )
        self.assertEqual(repr(state), "<ModelState: 'app.Model'>")

        project_state = ProjectState()
        project_state.add_model(state)
        with self.assertRaisesMessage(
            InvalidBasesError, "Cannot resolve bases for [<ModelState: 'app.Model'>]"
        ):
            project_state.apps