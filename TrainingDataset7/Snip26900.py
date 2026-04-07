def test_swappable(self):
        with isolate_lru_cache(apps.get_swappable_settings_name):
            changes = self.get_changes(
                [self.custom_user], [self.custom_user, self.author_with_custom_user]
            )
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(changes, "testapp", 0, ["CreateModel"])
        self.assertOperationAttributes(changes, "testapp", 0, 0, name="Author")
        self.assertMigrationDependencies(
            changes, "testapp", 0, [("__setting__", "AUTH_USER_MODEL")]
        )