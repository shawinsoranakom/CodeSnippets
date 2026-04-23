def test_circular_dependency_swappable(self):
        """
        #23322 - The dependency resolver knows to explicitly resolve
        swappable models.
        """
        with isolate_lru_cache(apps.get_swappable_settings_name):
            tenant = ModelState(
                "a",
                "Tenant",
                [
                    ("id", models.AutoField(primary_key=True)),
                    ("primary_address", models.ForeignKey("b.Address", models.CASCADE)),
                ],
                bases=(AbstractBaseUser,),
            )
            address = ModelState(
                "b",
                "Address",
                [
                    ("id", models.AutoField(primary_key=True)),
                    (
                        "tenant",
                        models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE),
                    ),
                ],
            )
            changes = self.get_changes([], [address, tenant])

        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "a", 2)
        self.assertOperationTypes(changes, "a", 0, ["CreateModel"])
        self.assertOperationTypes(changes, "a", 1, ["AddField"])
        self.assertMigrationDependencies(changes, "a", 0, [])
        self.assertMigrationDependencies(
            changes, "a", 1, [("a", "auto_1"), ("b", "auto_1")]
        )
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "b", 1)
        self.assertOperationTypes(changes, "b", 0, ["CreateModel"])
        self.assertMigrationDependencies(
            changes, "b", 0, [("__setting__", "AUTH_USER_MODEL")]
        )