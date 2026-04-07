def test_custom_default_manager_added_to_the_model_state(self):
        """
        When the default manager of the model is a custom manager,
        it needs to be added to the model state.
        """
        new_apps = Apps(["migrations"])
        custom_manager = models.Manager()

        class Author(models.Model):
            objects = models.TextField()
            authors = custom_manager

            class Meta:
                app_label = "migrations"
                apps = new_apps

        project_state = ProjectState.from_apps(new_apps)
        author_state = project_state.models["migrations", "author"]
        self.assertEqual(author_state.managers, [("authors", custom_manager)])