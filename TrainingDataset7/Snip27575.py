def test_render_unique_app_labels(self):
        """
        The ProjectState render method doesn't raise an
        ImproperlyConfigured exception about unique labels if two dotted app
        names have the same last part.
        """

        class A(models.Model):
            class Meta:
                app_label = "django.contrib.auth"

        class B(models.Model):
            class Meta:
                app_label = "vendor.auth"

        # Make a ProjectState and render it
        project_state = ProjectState()
        project_state.add_model(ModelState.from_model(A))
        project_state.add_model(ModelState.from_model(B))
        self.assertEqual(len(project_state.apps.get_models()), 2)