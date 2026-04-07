def test_circular_dependency_swappable_self(self):
        """
        #23322 - The dependency resolver knows to explicitly resolve
        swappable models.
        """
        with isolate_lru_cache(apps.get_swappable_settings_name):
            person = ModelState(
                "a",
                "Person",
                [
                    ("id", models.AutoField(primary_key=True)),
                    (
                        "parent1",
                        models.ForeignKey(
                            settings.AUTH_USER_MODEL,
                            models.CASCADE,
                            related_name="children",
                        ),
                    ),
                ],
            )
            changes = self.get_changes([], [person])
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "a", 1)
        self.assertOperationTypes(changes, "a", 0, ["CreateModel"])
        self.assertMigrationDependencies(changes, "a", 0, [])