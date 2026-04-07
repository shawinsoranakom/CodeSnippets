def test_custom_base_manager(self):
        new_apps = Apps(["migrations"])

        class Author(models.Model):
            manager1 = models.Manager()
            manager2 = models.Manager()

            class Meta:
                app_label = "migrations"
                apps = new_apps
                base_manager_name = "manager2"

        class Author2(models.Model):
            manager1 = models.Manager()
            manager2 = models.Manager()

            class Meta:
                app_label = "migrations"
                apps = new_apps
                base_manager_name = "manager1"

        project_state = ProjectState.from_apps(new_apps)

        author_state = project_state.models["migrations", "author"]
        self.assertEqual(author_state.options["base_manager_name"], "manager2")
        self.assertEqual(
            author_state.managers,
            [
                ("manager1", Author.manager1),
                ("manager2", Author.manager2),
            ],
        )

        author2_state = project_state.models["migrations", "author2"]
        self.assertEqual(author2_state.options["base_manager_name"], "manager1")
        self.assertEqual(
            author2_state.managers,
            [
                ("manager1", Author2.manager1),
            ],
        )