def test_render_project_dependencies(self):
        """
        The ProjectState render method correctly renders models
        to account for inter-model base dependencies.
        """
        new_apps = Apps()

        class A(models.Model):
            class Meta:
                app_label = "migrations"
                apps = new_apps

        class B(A):
            class Meta:
                app_label = "migrations"
                apps = new_apps

        class C(B):
            class Meta:
                app_label = "migrations"
                apps = new_apps

        class D(A):
            class Meta:
                app_label = "migrations"
                apps = new_apps

        class E(B):
            class Meta:
                app_label = "migrations"
                apps = new_apps
                proxy = True

        class F(D):
            class Meta:
                app_label = "migrations"
                apps = new_apps
                proxy = True

        # Make a ProjectState and render it
        project_state = ProjectState()
        project_state.add_model(ModelState.from_model(A))
        project_state.add_model(ModelState.from_model(B))
        project_state.add_model(ModelState.from_model(C))
        project_state.add_model(ModelState.from_model(D))
        project_state.add_model(ModelState.from_model(E))
        project_state.add_model(ModelState.from_model(F))
        final_apps = project_state.apps
        self.assertEqual(len(final_apps.get_models()), 6)

        # Now make an invalid ProjectState and make sure it fails
        project_state = ProjectState()
        project_state.add_model(ModelState.from_model(A))
        project_state.add_model(ModelState.from_model(B))
        project_state.add_model(ModelState.from_model(C))
        project_state.add_model(ModelState.from_model(F))
        with self.assertRaises(InvalidBasesError):
            project_state.apps