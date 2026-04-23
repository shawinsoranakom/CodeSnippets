def test_custom_default_manager_named_objects_with_false_migration_flag(self):
        """
        When a manager is added with a name of 'objects' but it does not
        have `use_in_migrations = True`, no migration should be added to the
        model state (#26643).
        """
        new_apps = Apps(["migrations"])

        class Author(models.Model):
            objects = models.Manager()

            class Meta:
                app_label = "migrations"
                apps = new_apps

        project_state = ProjectState.from_apps(new_apps)
        author_state = project_state.models["migrations", "author"]
        self.assertEqual(author_state.managers, [])