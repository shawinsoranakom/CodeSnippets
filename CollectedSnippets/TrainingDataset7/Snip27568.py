def test_custom_default_manager(self):
        new_apps = Apps(["migrations"])

        class Author(models.Model):
            manager1 = models.Manager()
            manager2 = models.Manager()

            class Meta:
                app_label = "migrations"
                apps = new_apps
                default_manager_name = "manager2"

        project_state = ProjectState.from_apps(new_apps)
        author_state = project_state.models["migrations", "author"]
        self.assertEqual(author_state.options["default_manager_name"], "manager2")
        self.assertEqual(author_state.managers, [("manager2", Author.manager1)])