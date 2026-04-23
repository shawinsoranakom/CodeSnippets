def test_real_apps(self):
        """
        Including real apps can resolve dangling FK errors.
        This test relies on the fact that contenttypes is always loaded.
        """
        new_apps = Apps()

        class TestModel(models.Model):
            ct = models.ForeignKey("contenttypes.ContentType", models.CASCADE)

            class Meta:
                app_label = "migrations"
                apps = new_apps

        # If we just stick it into an empty state it should fail
        project_state = ProjectState()
        project_state.add_model(ModelState.from_model(TestModel))
        with self.assertRaises(ValueError):
            project_state.apps

        # If we include the real app it should succeed
        project_state = ProjectState(real_apps={"contenttypes"})
        project_state.add_model(ModelState.from_model(TestModel))
        rendered_state = project_state.apps
        self.assertEqual(
            len(
                [
                    x
                    for x in rendered_state.get_models()
                    if x._meta.app_label == "migrations"
                ]
            ),
            1,
        )